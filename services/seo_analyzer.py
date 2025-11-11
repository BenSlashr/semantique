import re
import nltk
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import asyncio
from statistics import mean
from .cache_service import cache_service

# Télécharger les ressources NLTK nécessaires
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Import du service LLM (optionnel)
try:
    # Essai import relatif
    from .llm_keyword_filter import llm_filter
    LLM_AVAILABLE = True
    print(f"✅ LLM Service importé avec succès (relatif), enabled: {llm_filter.enabled if llm_filter else False}")
except ImportError:
    try:
        # Fallback import absolu
        from services.llm_keyword_filter import llm_filter
        LLM_AVAILABLE = True
        print(f"✅ LLM Service importé avec succès (absolu), enabled: {llm_filter.enabled if llm_filter else False}")
    except ImportError as e:
        llm_filter = None
        LLM_AVAILABLE = False
        print(f"⚠️ LLM Service non disponible: {e}")

class SEOAnalyzer:
    def __init__(self):
        self.french_stopwords = set(stopwords.words('french'))
        
        # Service LLM pour filtrage avancé (optionnel)
        self.llm_filter = llm_filter if LLM_AVAILABLE else None
        print(f"🔍 SEOAnalyzer.__init__: LLM_AVAILABLE={LLM_AVAILABLE}, llm_filter={self.llm_filter}")
        
        # Si import global a échoué, essai import dans __init__
        if not LLM_AVAILABLE:
            try:
                from services.llm_keyword_filter import llm_filter as local_llm_filter
                self.llm_filter = local_llm_filter
                print(f"✅ LLM Service importé dans __init__, enabled: {self.llm_filter.enabled if self.llm_filter else False}")
            except ImportError as e:
                print(f"⚠️ Import LLM dans __init__ échoué: {e}")
                self.llm_filter = None
        
        # Liste étendue de stopwords français incluant connecteurs et mots de liaison
        extended_stopwords = [
            # Articles et déterminants
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'ce', 'cette', 'ces', 'cet',
            'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'notre', 'nos', 'votre', 'vos', 'leur', 'leurs',
            
            # Conjonctions et connecteurs logiques
            'et', 'ou', 'ni', 'mais', 'car', 'donc', 'or', 'cependant', 'néanmoins', 'toutefois', 'pourtant',
            'ainsi', 'alors', 'aussi', 'également', 'de même', 'par ailleurs', 'en outre', 'en plus',
            'd ailleurs', 'par contre', 'en revanche', 'au contraire', 'tandis que', 'alors que',
            
            # Mots interrogatifs et relatifs
            'que', 'qui', 'quoi', 'dont', 'où', 'comment', 'pourquoi', 'quand', 'combien',
            'quel', 'quelle', 'quels', 'quelles', 'lequel', 'laquelle', 'lesquels', 'lesquelles',
            
            # Prépositions et locutions prépositionnelles
            'dans', 'sur', 'avec', 'par', 'pour', 'sans', 'sous', 'vers', 'chez', 'entre', 'parmi',
            'depuis', 'pendant', 'durant', 'après', 'avant', 'devant', 'derrière', 'près', 'loin',
            'à côté', 'au lieu', 'grâce à', 'face à', 'selon', 'malgré', 'contre', 'envers',
            'au dessus', 'au dessous', 'à travers', 'autour', 'le long', 'au cours',
            
            # Adverbes de liaison et de temps
            'plus', 'moins', 'très', 'bien', 'mal', 'mieux', 'beaucoup', 'peu', 'assez', 'trop',
            'encore', 'déjà', 'toujours', 'jamais', 'souvent', 'parfois', 'quelquefois',
            'maintenant', 'aujourd hui', 'hier', 'demain', 'bientôt', 'tard', 'tôt',
            'puis', 'ensuite', 'enfin', 'finalement', 'premièrement', 'deuxièmement',
            'd abord', 'en premier', 'en dernier', 'en fin', 'au début', 'à la fin',
            
            # Quantificateurs et intensificateurs
            'tout', 'tous', 'toute', 'toutes', 'chaque', 'plusieurs', 'quelques', 'certains', 'certaines',
            'autre', 'autres', 'même', 'mêmes', 'tel', 'telle', 'tels', 'telles',
            'aucun', 'aucune', 'nul', 'nulle', 'personne', 'rien', 'quelqu un', 'quelque chose',
            
            # Verbes auxiliaires et modaux
            'est', 'sont', 'était', 'étaient', 'sera', 'seront', 'avoir', 'être', 'faire', 'dire',
            'aller', 'voir', 'savoir', 'pouvoir', 'vouloir', 'venir', 'falloir', 'devoir', 'prendre',
            'peut', 'peuvent', 'doit', 'doivent', 'veut', 'veulent', 'va', 'vont',
            
            # Pronoms
            'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'je', 'tu', 'me', 'te', 'se', 'lui', 'leur',
            'moi', 'toi', 'soi', 'eux', 'y', 'en', 'cela', 'ça', 'celui', 'celle', 'ceux', 'celles',
            
            # Négations et affirmations
            'ne', 'pas', 'non', 'oui', 'si', 'point', 'guère', 'jamais', 'rien', 'personne',
            
            # Expressions de transition courantes
            'par exemple', 'c est à dire', 'en effet', 'en fait', 'en réalité', 'au fait',
            'à vrai dire', 'pour ainsi dire', 'si l on peut dire', 'en quelque sorte',
            'd une part', 'd autre part', 'en premier lieu', 'en second lieu',
            'par conséquent', 'en conséquence', 'par suite', 'de ce fait',
            'en somme', 'en résumé', 'en conclusion', 'pour conclure', 'bref',
            
            # Locutions adverbiales
            'à peu près', 'à peine', 'tout à fait', 'tout de même', 'quand même',
            'en même temps', 'à la fois', 'de plus en plus', 'de moins en moins',
            'peu à peu', 'petit à petit', 'de temps en temps', 'de temps à autre',
            
            # Mots de politesse et formules
            'merci', 'svp', 's il vous plaît', 'excusez moi', 'pardon', 'bonjour', 'bonsoir',
            'salut', 'au revoir', 'à bientôt', 'cordialement', 'sincèrement',
            
            # Prépositions composées
            'au', 'aux', 'à', 'en', 'du', 'des', 'de la', 'de l',
            
            # Expressions temporelles
            'au moment', 'à l époque', 'à cette époque', 'en ce moment', 'à présent',
            'actuellement', 'de nos jours', 'à l heure actuelle'
        ]
        
        self.french_stopwords.update(extended_stopwords)
        
        # Cache des stop words pour optimisation des validations
        self.validation_stop_words = frozenset({
            'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'ce', 'ces', 'se', 'sa', 'son', 'ses',
            'sur', 'sous', 'dans', 'avec', 'sans', 'pour', 'par', 'vers', 'chez', 'entre', 'depuis',
            'et', 'ou', 'ni', 'mais', 'car', 'donc', 'or', 'comme', 'que', 'qui', 'dont', 'où',
            'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'je', 'tu', 'me', 'te', 'se', 'lui', 'leur',
            'mon', 'ton', 'ma', 'ta', 'mes', 'tes', 'nos', 'vos', 'leur', 'leurs', 'votre', 'notre',
            'est', 'sont', 'était', 'étaient', 'sera', 'seront', 'avoir', 'être', 'faire', 'dire',
            'aller', 'voir', 'savoir', 'pouvoir', 'vouloir', 'venir', 'falloir', 'devoir', 'prendre',
            'plus', 'moins', 'très', 'bien', 'mal', 'mieux', 'beaucoup', 'peu', 'assez', 'trop',
            'tout', 'tous', 'toute', 'toutes', 'autre', 'autres', 'même', 'mêmes', 'tel', 'telle',
            'à', 'au', 'aux', 'en', 'y', 'ne', 'pas', 'non', 'oui', 'si', 'peut', 'peuvent'
        })
        
        # Cache des exceptions SEO
        self.seo_exceptions = frozenset({'seo', 'web', 'app', 'cms', 'api', 'roi', 'kpi', 'b2b', 'b2c'})
        
        # Cache des patterns invalides étendus
        self.invalid_bigram_patterns = frozenset([
            # Prépositions + articles
            'à la', 'à le', 'à les', 'de la', 'de le', 'de les', 'du côté', 'au niveau',
            'en tant', 'par rapport', 'grâce à', 'face à', 'selon les', 'selon le', 'selon la',
            'parmi les', 'parmi le', 'au sein', 'au cours', 'au lieu', 'en plus', 'en effet',
            
            # Connecteurs logiques
            'ainsi que', 'alors que', 'tandis que', 'bien que', 'quand même', 'tout de',
            'de même', 'par ailleurs', 'en outre', 'd ailleurs', 'par contre', 'en revanche',
            'au contraire', 'par conséquent', 'en conséquence', 'de ce', 'en somme',
            
            # Quantificateurs vides
            'quelques uns', 'certains de', 'plusieurs de', 'beaucoup de', 'peu de', 'assez de',
            'trop de', 'plus de', 'moins de', 'autant de', 'tant de',
            
            # Expressions temporelles vides
            'au moment', 'à l époque', 'en ce', 'à présent', 'de nos', 'à cette',
            'pendant que', 'durant que', 'depuis que', 'avant que', 'après que',
            
            # Mots interrogatifs + prépositions
            'quels sont', 'quelle est', 'quel est', 'quelles sont', 'comment se',
            'pourquoi les', 'où se', 'quand les', 'combien de',
            
            # Expressions courantes vides de sens
            'aussi bien', 'par exemple', 'en fait', 'en réalité', 'à vrai',
            'tout à', 'quand même', 'tout de', 'petit à', 'peu à',
            'de temps', 'en temps', 'à côté', 'au lieu', 'grâce à'
        ])
        
        self.invalid_trigram_starts = frozenset([
            # Pronoms + verbes être/avoir
            'il est', 'elle est', 'nous sommes', 'vous êtes', 'ils sont', 'elles sont', 'c est', 'ce sont',
            'il a', 'elle a', 'ils ont', 'elles ont', 'nous avons', 'vous avez', 'on a', 'on est',
            
            # Expressions interrogatives
            'qu est ce', 'est ce que', 'comment est', 'pourquoi est', 'où est', 'quand est',
            'quel est le', 'quelle est la', 'quels sont les', 'quelles sont les',
            
            # Connecteurs en début
            'ainsi que les', 'alors que les', 'bien que les', 'comme les', 'si les',
            'lorsque les', 'pendant que les', 'après que les', 'avant que les'
        ])
        
        self.invalid_trigram_ends = frozenset([
            # Connecteurs en fin
            'de plus en', 'en plus de', 'en effet de', 'par exemple de', 'en fait de',
            'ainsi que de', 'alors que de', 'bien que de', 'grâce à la', 'face à la',
            'selon les experts', 'parmi les plus', 'au sein de', 'au cours de',
            
            # Expressions temporelles vides
            'à cette époque', 'en ce moment', 'à l heure', 'de nos jours', 'actuellement en',
            'pendant ce temps', 'en même temps', 'à la fois', 'tout de même',
            
            # Quantificateurs vides
            'beaucoup de plus', 'peu de plus', 'assez de plus', 'trop de plus',
            'plus de la', 'moins de la', 'autant de la'
        ])
        
        # Cache regex compilées pour éviter recompilation
        self.regex_punctuation = re.compile(r'[^\w\s]')
        self.regex_whitespace = re.compile(r'\s+')
        
    async def analyze_competition(self, query: str, serp_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse complète de la concurrence SEO avec cache 7 jours"""
        
        # 🚀 CACHE: Vérification du cache d'abord
        cached_analysis = cache_service.get("seo_analysis", query)
        if cached_analysis is not None:
            print(f"📦 Cache HIT: Analyse SEO '{query}' (économie calculs)")
            return cached_analysis
        
        # Réinitialisation des caches pour chaque nouvelle analyse
        self._text_cache = {}
        
        # Si pas de résultats réels, utiliser les données de démonstration
        if not serp_results or not serp_results.get('organic_results'):
            return self._get_demo_analysis(query)
        
        # Extraction des données organiques et éléments SERP
        organic_results = serp_results.get('organic_results', [])
        paa_questions = serp_results.get('paa', [])
        related_searches = serp_results.get('related_searches', [])
        inline_videos = serp_results.get('inline_videos', [])
        
        all_content = self._extract_all_content(organic_results)
        query_words = self._clean_text(query).split()
        
        keywords_obligatoires = self._extract_required_keywords(all_content, query_words)
        keywords_complementaires = self._extract_complementary_keywords(all_content, keywords_obligatoires)
        
        # 🤖 Filtrage LLM optionnel (amélioration qualité des mots-clés)
        keywords_obligatoires = await self._enhance_keywords_with_llm(keywords_obligatoires, query, "required")
        keywords_complementaires = await self._enhance_keywords_with_llm(keywords_complementaires, query, "complementary")
        
        # Ajout des statistiques min-max pour chaque mot-clé
        keywords_obligatoires = self._add_minmax_stats(keywords_obligatoires, organic_results)
        keywords_complementaires = self._add_minmax_stats(keywords_complementaires, organic_results)
        ngrams = self._extract_ngrams(all_content, query)
        
        # Extraction des groupes de mots-clés
        bigrams = self._extract_bigrams(all_content, query)
        trigrams = self._extract_trigrams(all_content, query)
        questions = self._generate_questions(query, keywords_obligatoires, paa_questions)
        
        concurrence_analysee = self._analyze_competitors(organic_results, keywords_obligatoires, keywords_complementaires)
        
        score_target = self._calculate_target_score(concurrence_analysee)
        mots_requis = self._calculate_required_words(concurrence_analysee)
        max_suroptimisation = self._calculate_max_overoptimization(keywords_obligatoires)
        
        type_analysis = self._analyze_content_types(organic_results)
        word_stats = self._calculate_word_statistics(organic_results)
        
        final_analysis = {
            "query": query,
            "score_target": score_target,
            "mots_requis": mots_requis,
            "KW_obligatoires": keywords_obligatoires,
            "KW_complementaires": keywords_complementaires,
            "ngrams": ngrams,
            "max_suroptimisation": max_suroptimisation,
            "questions": questions,
            "paa": paa_questions,
            "related_searches": related_searches,
            "inline_videos": inline_videos,
            "bigrams": bigrams,
            "trigrams": trigrams,
            "type_editorial": type_analysis["editorial"],
            "type_catalogue": type_analysis["catalogue"],
            "type_fiche_produit": type_analysis["fiche_produit"],
            "mots_uniques_min_max_moyenne": word_stats,
            "concurrence": concurrence_analysee
        }
        
        # 💾 CACHE: Stocker l'analyse pour 7 jours
        cache_service.set("seo_analysis", final_analysis, query)
        print(f"💾 Cache MISS: Analyse SEO '{query}' → stocké 7j")
        
        return final_analysis
    
    def _extract_all_content(self, serp_results: List[Dict[str, Any]]) -> str:
        """Extrait tout le contenu textuel des résultats SERP"""
        all_text = []
        
        for result in serp_results:
            text_parts = [
                result.get("title", ""),
                result.get("h1", ""),
                result.get("h2", ""),
                result.get("h3", ""),
                result.get("content", ""),
                result.get("snippet", "")
            ]
            all_text.extend([part for part in text_parts if part])
        
        return " ".join(all_text)
    
    def _clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte avec cache pour optimisation"""
        if not text:
            return ""
            
        # Cache basique pour éviter recalculer les mêmes textes
        text_hash = hash(text)
        if hasattr(self, '_text_cache') and text_hash in self._text_cache:
            return self._text_cache[text_hash]
        
        # Filtrage des patterns techniques/CSS/SVG avant nettoyage
        text = self._filter_technical_content(text)
        
        # Utilisation des regex précompilées
        cleaned = self.regex_punctuation.sub(' ', text.lower())
        cleaned = self.regex_whitespace.sub(' ', cleaned).strip()
        
        # Cache le résultat si le cache n'est pas trop gros
        if not hasattr(self, '_text_cache'):
            self._text_cache = {}
        if len(self._text_cache) < 1000:  # Limite du cache
            self._text_cache[text_hash] = cleaned
        
        return cleaned
    
    def _filter_technical_content(self, text: str) -> str:
        """Filtre le contenu technique (CSS, SVG, code) du texte"""
        import re
        
        # Patterns CSS/SVG/techniques à exclure
        technical_patterns = [
            # Séquences numériques techniques (comme "000 stroke width 0px")
            r'\b\d{3,}\s+\w+\s+\w+\s+\d+px\b',  # Pattern spécifique "000 stroke width 0px"
            r'\b\d+\s+stroke\s+width\s+\d+px\b', # Pattern général stroke width
            r'\b\d+\s+fill\s+\d+\b',             # Pattern fill numérique
            
            # CSS properties et valeurs
            r'\b\d+px\b',  # pixels
            r'\b\d+%\b',   # pourcentages (sauf si dans contexte métier)
            r'\b\d+rem\b', # rem units
            r'\b\d+em\b',  # em units
            r'\brgb\([^)]+\)',  # couleurs RGB
            r'\b#[0-9a-fA-F]{3,6}\b',  # couleurs hex
            r'\bstroke\b(?!\s+(?:de|d|du))',  # SVG stroke (sauf "stroke de")
            r'\bfill\b(?!\s+(?:de|d|du))',    # SVG fill (sauf "fill de")
            r'\bwidth\s*:\s*\d+',  # width CSS
            r'\bheight\s*:\s*\d+', # height CSS
            r'\bmargin\s*:\s*\d+',  # margin CSS
            r'\bpadding\s*:\s*\d+', # padding CSS
            r'\bborder\s*:\s*\d+',  # border CSS
            r'\bbackground\s*:\s*\w+', # background CSS
            
            # SVG spécifiques
            r'\bviewBox\b',
            r'\bclipPath\b',
            r'\bstroke-width\b',
            r'\bstroke-dasharray\b',
            r'\bfill-rule\b',
            
            # Attributs HTML techniques
            r'\bclass\s*=\s*["\'][^"\']*["\']',
            r'\bid\s*=\s*["\'][^"\']*["\']',
            r'\bdata-[a-zA-Z-]+\s*=\s*["\'][^"\']*["\']',
            r'\baria-[a-zA-Z-]+\s*=\s*["\'][^"\']*["\']',
            
            # Codes techniques divers
            r'\b[0-9a-fA-F]{8,}\b',  # Hash/ID longs
            r'\b\w+\.\w+\.\w+\b',    # Noms de domaine/packages
            r'\bversion\s*\d+\.\d+\b', # Numéros de version
            
            # Mots techniques isolés (plus ciblés)
            r'\bcls\s+\d+\b',  # cls suivi de nombre
            r'\b(svg|xml|css|js|json|api|url|uri|href|src|alt|meta|link|script|style|div|span|img|iframe|canvas|doctype)\b',
        ]
        
        # Applique tous les patterns
        for pattern in technical_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Nettoie les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_required_keywords(self, content: str, query_words: List[str]) -> List[List[Any]]:
        """Extrait les mots-clés obligatoires avec leurs statistiques"""
        # Utiliser le mode inclusif pour capturer tous les mots
        words = self._tokenize_and_filter(content, include_short_words=True)
        word_freq = Counter(words)
        
        # Calcul TF-IDF pour l'importance
        tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words=list(self.french_stopwords))
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform([content])
            feature_names = tfidf_vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            tfidf_dict = dict(zip(feature_names, tfidf_scores))
        except:
            tfidf_dict = {}
        
        # Sélection des mots-clés obligatoires
        keywords = []
        
        # 1. D'abord, forcer l'inclusion des mots de la requête
        for query_word in query_words:
            if query_word in word_freq:
                freq = word_freq[query_word]
                tfidf_score = tfidf_dict.get(query_word, 0)
                importance = int(tfidf_score * 100) if tfidf_score > 0 else freq
                importance += 30  # Bonus important pour les mots de la requête
                keywords.append([query_word, freq, importance])
                print(f"🎯 Mot de requête ajouté: {query_word} (fréq: {freq}, importance: {importance})")
        
        # 2. Ensuite, ajouter les autres mots-clés
        for word, freq in word_freq.most_common(50):
            # Skip si déjà ajouté comme mot de requête
            if word in query_words:
                continue
                
            if len(word) > 2 and freq > 1:  # Garder 3+ caractères pour les autres mots
                tfidf_score = tfidf_dict.get(word, 0)
                importance = int(tfidf_score * 100) if tfidf_score > 0 else freq
                keywords.append([word, freq, importance])
        
        # Trie par importance décroissante
        keywords.sort(key=lambda x: x[2], reverse=True)
        return keywords[:45]  # Top 45 comme dans l'exemple
    
    def _tokenize_and_filter(self, text: str, include_short_words: bool = False) -> List[str]:
        """Tokenise et filtre le texte"""
        clean_text = self._clean_text(text)
        words = word_tokenize(clean_text, language='french')
        
        # Filtre les mots courts et les stop words
        if include_short_words:
            # Mode inclusif pour les mots de la requête
            filtered_words = [
                word for word in words 
                if len(word) > 1 and word not in self.french_stopwords
            ]
        else:
            filtered_words = [
                word for word in words 
                if len(word) > 2 and word not in self.french_stopwords
            ]
        
        return filtered_words
    
    def _extract_complementary_keywords(self, content: str, required_keywords: List[List[Any]]) -> List[List[Any]]:
        """Extrait les mots-clés complémentaires"""
        words = self._tokenize_and_filter(content)
        word_freq = Counter(words)
        
        # Mots déjà utilisés dans les obligatoires
        required_words = [kw[0] for kw in required_keywords]
        
        complementary = []
        for word, freq in word_freq.most_common(200):
            if word not in required_words and len(word) > 3:
                # Score basé sur la fréquence et la longueur
                score = min(freq + len(word) - 3, 33)
                complementary.append([word, freq, score])
        
        # Trie par score décroissant
        complementary.sort(key=lambda x: x[2], reverse=True)
        return complementary[:100]  # Top 100 mots complémentaires
    
    def _extract_ngrams(self, content: str, query: str) -> List[List[Any]]:
        """Extrait les n-grammes les plus pertinents avec scores d'importance"""
        clean_text = self._clean_text(content)
        words = clean_text.split()
        query_words = self._clean_text(query).split()
        
        # Extraction des expressions de 4-5 mots (plus longues que bigrams/trigrams)
        ngrams_4 = []
        ngrams_5 = []
        
        # N-grammes de 4 mots
        for i in range(len(words) - 3):
            ngram = f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]}"
            if len(ngram) > 15 and self._is_valid_ngram(ngram):
                ngrams_4.append(ngram)
        
        # N-grammes de 5 mots
        for i in range(len(words) - 4):
            ngram = f"{words[i]} {words[i+1]} {words[i+2]} {words[i+3]} {words[i+4]}"
            if len(ngram) > 20 and self._is_valid_ngram(ngram):
                ngrams_5.append(ngram)
        
        # Compte les occurrences
        all_ngrams = ngrams_4 + ngrams_5
        ngram_counts = Counter(all_ngrams)
        
        # Création de la liste avec scores
        ngram_keywords = []
        
        for ngram, freq in ngram_counts.most_common(100):
            if freq > 1:  # Au moins 2 occurrences
                # Calcul de l'importance
                importance = freq * 4  # Base sur la fréquence
                
                # Bonus majeur si contient des mots de la requête
                ngram_words = ngram.split()
                query_match_count = sum(1 for word in ngram_words if word in query_words)
                importance += query_match_count * 25
                
                # Bonus pour expressions sémantiquement riches
                semantic_words = ['comment', 'pourquoi', 'quand', 'guide', 'conseil', 'astuce', 'méthode', 'technique', 'stratégie', 'comparaison', 'différence', 'avantage', 'inconvénient', 'bienfait', 'effet', 'résultat']
                if any(word in ngram.lower() for word in semantic_words):
                    importance += 15
                
                # Bonus pour longueur (expressions plus descriptives)
                if len(ngram) > 30:
                    importance += 10
                
                ngram_keywords.append([ngram, freq, importance])
        
        # Trie par importance décroissante
        ngram_keywords.sort(key=lambda x: x[2], reverse=True)
        
        # Phase 1: Déduplication et regroupement des expressions similaires
        deduplicated_ngrams = self._deduplicate_ngrams(ngram_keywords)
        
        return deduplicated_ngrams[:25]  # Top 25 n-grammes dédupliqués
    
    def _is_valid_ngram(self, ngram: str) -> bool:
        """Valide si un n-gramme long est pertinent - Version améliorée pour Phase 1"""
        words = ngram.split()
        
        # Doit avoir au moins 4 mots
        if len(words) < 4:
            return False
        
        # Mots vides étendus à éviter
        stop_words = {
            'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'et', 'ou', 'à', 'au', 'aux', 'en',
            'dans', 'sur', 'avec', 'par', 'pour', 'sans', 'sous', 'vers', 'chez', 'depuis',
            'pendant', 'après', 'avant', 'entre', 'contre', 'selon', 'malgré', 'durant'
        }
        
        # Mots de liaison qui rendent l'expression incomplète
        incomplete_words = {'pour', 'après', 'avant', 'pendant', 'durant', 'selon', 'malgré', 'contre'}
        
        # Ne doit pas commencer ou finir par un mot vide ou incomplet
        if words[0] in stop_words or words[-1] in stop_words:
            return False
        
        if words[0] in incomplete_words or words[-1] in incomplete_words:
            return False
        
        # Évite les n-grammes avec trop de mots vides (max 25% au lieu de 30%)
        stop_word_count = sum(1 for word in words if word in stop_words)
        if stop_word_count / len(words) > 0.25:
            return False
        
        # Évite les patterns trop répétitifs (75% au lieu de 70%)
        unique_words = set(words)
        if len(unique_words) < len(words) * 0.75:
            return False
        
        # Évite les expressions avec des mots trop courts répétés
        short_words = [word for word in words if len(word) <= 2]
        if len(short_words) > len(words) * 0.3:  # Max 30% de mots très courts
            return False
        
        # Bonus: Favorise les expressions avec des mots métier/techniques
        technical_indicators = [
            'formation', 'cursus', 'diplôme', 'certification', 'spécialisation',
            'débouchés', 'carrière', 'métier', 'profession', 'emploi',
            'compétences', 'skills', 'expertise', 'technique', 'méthode',
            'stratégie', 'management', 'gestion', 'finance', 'marketing'
        ]
        
        # Si contient des mots techniques, c'est plus susceptible d'être pertinent
        has_technical_words = any(word.lower() in technical_indicators for word in words)
        
        return True
    
    def _deduplicate_ngrams(self, ngram_keywords: List[List[Any]]) -> List[List[Any]]:
        """
        Phase 1: Déduplication et regroupement des expressions similaires
        
        Stratégies implémentées:
        1. Déduplication par chevauchement de mots
        2. Regroupement des expressions similaires
        3. Conservation de l'expression la plus représentative par groupe
        """
        if not ngram_keywords:
            return []
        
        print(f"🔧 Déduplication: {len(ngram_keywords)} n-grams avant traitement")
        
        deduplicated = []
        processed_groups = []
        
        for current_ngram, current_freq, current_importance in ngram_keywords:
            current_words = set(current_ngram.split())
            
            # Chercher un groupe existant avec chevauchement significatif
            found_group = False
            
            for group_idx, (group_ngram, group_freq, group_importance) in enumerate(processed_groups):
                group_words = set(group_ngram.split())
                
                # Calculer le chevauchement (intersection / union) - Jaccard similarity
                intersection = current_words & group_words
                union = current_words | group_words
                jaccard_similarity = len(intersection) / len(union) if union else 0
                
                # Calculer aussi le chevauchement simple (mots en commun / mots total)
                min_length = min(len(current_words), len(group_words))
                simple_overlap = len(intersection) / min_length if min_length > 0 else 0
                
                # Conditions de similarité plus flexibles:
                # 1. Jaccard > 50% (expressions très similaires)
                # 2. OU chevauchement simple > 60% (beaucoup de mots en commun)
                # 3. OU même racine sémantique (école/écoles, commerce/commerciale)
                is_similar = (jaccard_similarity > 0.5 or 
                             simple_overlap > 0.6 or
                             self._have_same_semantic_root(current_ngram, group_ngram))
                
                if is_similar:
                    found_group = True
                    
                    # Garder l'expression la plus représentative (score le plus élevé)
                    if current_importance > group_importance:
                        # Remplacer l'expression du groupe par la nouvelle
                        processed_groups[group_idx] = (current_ngram, current_freq + group_freq, current_importance)
                        print(f"🔄 Remplacement: '{group_ngram}' → '{current_ngram}' (score: {group_importance} → {current_importance})")
                    else:
                        # Juste additionner la fréquence
                        processed_groups[group_idx] = (group_ngram, group_freq + current_freq, group_importance)
                        print(f"📈 Fusion: '{current_ngram}' dans '{group_ngram}' (fréq: {group_freq} + {current_freq})")
                    break
            
            # Si aucun groupe similaire trouvé, créer un nouveau groupe
            if not found_group:
                processed_groups.append((current_ngram, current_freq, current_importance))
        
        # Convertir les groupes en format final
        for ngram, freq, importance in processed_groups:
            deduplicated.append([ngram, freq, importance])
        
        # Re-trier par importance après fusion
        deduplicated.sort(key=lambda x: x[2], reverse=True)
        
        print(f"✅ Déduplication terminée: {len(ngram_keywords)} → {len(deduplicated)} n-grams (-{len(ngram_keywords) - len(deduplicated)})")
        
        return deduplicated
    
    def _have_same_semantic_root(self, ngram1: str, ngram2: str) -> bool:
        """Détecte si deux n-grams ont la même racine sémantique"""
        # Normalisation des variantes communes
        semantic_groups = {
            'école': ['école', 'écoles', 'ecole', 'ecoles'],
            'commerce': ['commerce', 'commerciale', 'commerciales', 'commerciaux'],
            'formation': ['formation', 'formations', 'formative', 'former'],
            'étude': ['étude', 'études', 'étudiant', 'étudiants'],
            'diplôme': ['diplôme', 'diplômes', 'diplômé', 'diplômés'],
            'entreprise': ['entreprise', 'entreprises', 'entrepreneurial'],
            'management': ['management', 'manager', 'managériale', 'gestion'],
            'carrière': ['carrière', 'carrières', 'professionnel', 'profession'],
            'bac': ['bac', 'baccalauréat', 'bachelor'],
            'licence': ['licence', 'licences', 'licensing'],
            'master': ['master', 'masters', 'mastère'],
            'post': ['post', 'après', 'suite']
        }
        
        words1 = set(ngram1.lower().split())
        words2 = set(ngram2.lower().split())
        
        # Chercher des mots appartenant au même groupe sémantique
        for root, variants in semantic_groups.items():
            variants_set = set(variants)
            
            # Si les deux n-grams contiennent des variantes du même concept
            if (words1 & variants_set) and (words2 & variants_set):
                # Vérifier qu'ils ont aussi d'autres mots en commun
                common_words = words1 & words2
                if len(common_words) >= 2:  # Au moins 2 mots en commun
                    return True
        
        return False
    
    def _extract_bigrams(self, content: str, query: str) -> List[List[Any]]:
        """Extrait les groupes de mots-clés de 2 mots avec analyse de leur importance - Version optimisée"""
        clean_text = self._clean_text(content)
        words = clean_text.split()
        query_words = self._clean_text(query).split()
        
        # Extraction optimisée avec pré-filtrage
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1) 
                  if len(f"{words[i]} {words[i+1]}") > 6]
        
        # Comptage rapide des occurrences
        bigram_counts = Counter(bigrams)
        
        # Cache des mots SEO pour éviter les recherches répétées
        seo_words_set = frozenset(['seo', 'référencement', 'google', 'naturel', 'optimisation', 'ranking'])
        query_words_set = frozenset(query_words)
        
        # Traitement optimisé avec pré-filtrage
        bigram_keywords = []
        filtered_count = 0
        
        for bigram, freq in bigram_counts.most_common(200):
            if freq > 1 and self._is_valid_bigram(bigram):
                # Calcul optimisé de l'importance
                importance = freq * 2
                
                # Bonus optimisé pour mots de requête (intersection de sets)
                bigram_words_set = frozenset(bigram.split())
                if bigram_words_set & query_words_set:
                    importance += 15
                
                # Bonus SEO optimisé
                if any(seo_word in bigram.lower() for seo_word in seo_words_set):
                    importance += 10
                
                bigram_keywords.append([bigram, freq, importance])
            else:
                filtered_count += 1
        
        # Tri par importance décroissante
        bigram_keywords.sort(key=lambda x: x[2], reverse=True)
        
        print(f"🔍 Bigrams: {len(bigram_keywords)} gardés, {filtered_count} filtrés sur {len(bigram_counts)} analysés")
        
        return bigram_keywords[:25]  # Top 25 bigrams
    
    def _extract_trigrams(self, content: str, query: str) -> List[List[Any]]:
        """Extrait les groupes de mots-clés de 3 mots avec analyse de leur importance - Version optimisée"""
        clean_text = self._clean_text(content)
        words = clean_text.split()
        query_words = self._clean_text(query).split()
        
        # Extraction optimisée avec pré-filtrage
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words) - 2) 
                   if len(f"{words[i]} {words[i+1]} {words[i+2]}") > 10]
        
        # Comptage rapide des occurrences
        trigram_counts = Counter(trigrams)
        
        # Cache des mots SEO et requête pour optimisation
        seo_words_set = frozenset(['seo', 'référencement', 'google', 'naturel', 'optimisation', 'ranking'])
        query_words_set = frozenset(query_words)
        
        # Traitement optimisé
        trigram_keywords = []
        filtered_count = 0
        
        for trigram, freq in trigram_counts.most_common(150):
            if freq > 1 and self._is_valid_trigram(trigram):
                # Calcul optimisé de l'importance
                importance = freq * 3
                
                # Bonus optimisé pour mots de requête (intersection de sets)
                trigram_words_set = frozenset(trigram.split())
                if trigram_words_set & query_words_set:
                    importance += 20
                
                # Bonus SEO optimisé
                if any(seo_word in trigram.lower() for seo_word in seo_words_set):
                    importance += 15
                
                # Bonus longueur optimisé (évite len() répété)
                if len(trigram) > 20:
                    importance += 5
                
                trigram_keywords.append([trigram, freq, importance])
            else:
                filtered_count += 1
        
        # Tri par importance décroissante
        trigram_keywords.sort(key=lambda x: x[2], reverse=True)
        
        print(f"🔍 Trigrams: {len(trigram_keywords)} gardés, {filtered_count} filtrés sur {len(trigram_counts)} analysés")
        
        return trigram_keywords[:20]  # Top 20 trigrams
    
    def _is_valid_bigram(self, bigram: str) -> bool:
        """Valide si un bigram est un vrai groupe de mots-clés - Version optimisée"""
        words = bigram.split()
        if len(words) != 2:
            return False
        
        # Check direct dans les patterns invalides (plus rapide)
        if bigram in self.invalid_bigram_patterns:
            return False
        
        # Évite les bigrams commençant ou finissant par des mots vides (utilise le cache)
        if words[0] in self.validation_stop_words or words[1] in self.validation_stop_words:
            return False
        
        # Vérification rapide des mots trop courts (utilise le cache SEO)
        for word in words:
            if len(word) < 3 and word.lower() not in self.seo_exceptions:
                return False
        
        return True
    
    def _is_valid_trigram(self, trigram: str) -> bool:
        """Valide si un trigram est une vraie expression de mots-clés - Version optimisée"""
        words = trigram.split()
        if len(words) != 3:
            return False
        
        # Évite les trigrams commençant ou finissant par des mots vides (cache)
        if words[0] in self.validation_stop_words or words[2] in self.validation_stop_words:
            return False
        
        # Autorise un seul mot vide au milieu (ex: "agence de communication")
        stop_count = sum(1 for word in words if word in self.validation_stop_words)
        if stop_count > 1:
            return False
        
        # Si un mot vide est présent, il doit être au milieu
        if stop_count == 1 and words[1] not in self.validation_stop_words:
            return False
        
        # Vérification rapide des mots trop courts (cache SEO)
        for word in words:
            if len(word) < 3 and word.lower() not in self.seo_exceptions and word not in self.validation_stop_words:
                return False
        
        # Check rapide des patterns invalides (cache)
        bigram_start = f"{words[0]} {words[1]}"
        bigram_end = f"{words[1]} {words[2]}"
        
        if bigram_start in self.invalid_trigram_starts or bigram_end in self.invalid_trigram_ends:
            return False
        
        return True
    
    def _add_minmax_stats(self, keywords: List[List[Any]], organic_results: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        🎯 Calcule les recommandations statistiques d'occurrences basées sur les top performers

        📊 MÉTHODE AMÉLIORÉE (Option 4 + 5) :
        - Analyse TOP 20 résultats (au lieu de TOP 10)
        - Target = moyenne(médiane + Q3) pour viser les performers
        - Fourchette : [target × 0.9, target × 1.25]
        - Minimums de sécurité augmentés si pas de données
        """
        enhanced_keywords = []

        # Cache pour éviter de retokeniser le même contenu plusieurs fois
        content_cache = {}

        for keyword_info in keywords:
            keyword = keyword_info[0]
            freq = keyword_info[1]
            importance = keyword_info[2]
            keyword_lower = keyword.lower()

            # Analyser les occurrences dans chaque page concurrente (TOP 20)
            occurrences = []

            for i, result in enumerate(organic_results[:20]):  # TOP 20 au lieu de TOP 10
                # Utilise le cache pour éviter retokenisation
                if i not in content_cache:
                    content = result.get("content", "") + " " + result.get("title", "") + " " + result.get("h1", "") + " " + result.get("h2", "") + " " + result.get("h3", "")
                    content_cache[i] = self._tokenize_and_filter(content.lower(), include_short_words=True)

                count = content_cache[i].count(keyword_lower)
                if count > 0:  # Ne compter que les pages qui utilisent le mot-clé
                    occurrences.append(count)

            # Calcul statistiques recommandées
            if len(occurrences) >= 2:
                # Calculs statistiques réels
                occurrences.sort()
                median = self._calculate_median(occurrences)
                q1, q3 = self._calculate_quartiles(occurrences)

                # 🎯 NOUVEAU : Target = moyenne(médiane + Q3) pour viser les performers
                target = int((median + q3) / 2)

                # Fourchette décalée vers le haut : [target × 0.9, target × 1.25]
                target_min = max(1, int(target * 0.9))
                target_max = int(target * 1.25)

                # Ajustement si fourchette trop étroite
                if target_max - target_min < 4:
                    target_max = target_min + 4

            elif len(occurrences) == 1:
                # Une seule occurrence trouvée - estimation plus ambitieuse
                single_occ = occurrences[0]
                target = int(single_occ * 1.1)  # +10% au lieu de rester à 1.0
                target_min = max(1, int(target * 0.85))
                target_max = int(target * 1.3)
            else:
                # 🚀 NOUVEAU : Minimums de sécurité augmentés
                if importance > 70:
                    target = max(12, freq // 8)   # au lieu de max(8, freq // 10)
                elif importance > 40:
                    target = max(8, freq // 15)   # au lieu de max(4, freq // 20)
                else:
                    target = max(5, freq // 25)   # au lieu de max(2, freq // 30)

                target_min = max(1, target - 2)
                target_max = target + 4

            # Format : [mot-clé, target_recommandé, importance, fourchette_min, fourchette_max]
            enhanced_keywords.append([keyword, target, importance, target_min, target_max])

        return enhanced_keywords
    
    def _calculate_median(self, values):
        """Calcule la médiane d'une liste de valeurs"""
        if not values:
            return 0
        values = sorted(values)
        n = len(values)
        if n % 2 == 0:
            return (values[n//2 - 1] + values[n//2]) / 2
        else:
            return values[n//2]
    
    def _calculate_quartiles(self, values):
        """Calcule Q1 et Q3 d'une liste de valeurs"""
        if len(values) < 2:
            return values[0] if values else 0, values[0] if values else 0
        
        values = sorted(values)
        n = len(values)
        
        # Q1 (25ème percentile)
        q1_pos = (n + 1) * 0.25
        if q1_pos.is_integer():
            q1 = values[int(q1_pos) - 1]
        else:
            lower = int(q1_pos) - 1
            upper = lower + 1
            weight = q1_pos - int(q1_pos)
            q1 = values[lower] * (1 - weight) + values[min(upper, n-1)] * weight
        
        # Q3 (75ème percentile)
        q3_pos = (n + 1) * 0.75
        if q3_pos.is_integer():
            q3 = values[int(q3_pos) - 1]
        else:
            lower = int(q3_pos) - 1
            upper = lower + 1
            weight = q3_pos - int(q3_pos)
            q3 = values[lower] * (1 - weight) + values[min(upper, n-1)] * weight
        
        return int(q1), int(q3)
    
    def _generate_questions(self, query: str, keywords: List[List[Any]], paa_questions: List[str] = None) -> str:
        """Génère des questions pertinentes basées sur la requête, les mots-clés et les PAA"""
        questions = []
        
        # Ajout des questions PAA en priorité (données réelles de Google)
        if paa_questions:
            questions.extend(paa_questions)
        
        # Questions générées automatiquement
        auto_questions = [
            f"Qu'est-ce que {query} ?",
            f"Comment choisir {query} ?",
            f"Pourquoi utiliser {query} ?",
            f"Quand prendre {query} ?",
            f"Quel est le meilleur {query} ?",
            f"Comment fonctionne {query} ?",
            f"Quels sont les bienfaits de {query} ?",
            f"Quelle est la différence entre {query} ?",
            f"Comment prendre {query} ?",
            f"Faut-il prendre {query} ?"
        ]
        questions.extend(auto_questions)
        
        # Questions basées sur les mots-clés principaux
        top_keywords = [kw[0] for kw in keywords[:5]]
        for keyword in top_keywords:
            questions.extend([
                f"Pourquoi {keyword} est important ?",
                f"Comment {keyword} fonctionne ?",
                f"Quel est l'effet de {keyword} ?",
                f"Quand utiliser {keyword} ?"
            ])
        
        return ";".join(questions[:60])
    
    def _analyze_competitors(self, serp_results: List[Dict[str, Any]], keywords_obligatoires: List[List[Any]], keywords_complementaires: List[List[Any]]) -> List[Dict[str, Any]]:
        """
        🔍 ANALYSE DÉTAILLÉE DE CHAQUE CONCURRENT AVEC SEUILS ADAPTATIFS
        
        📊 Métriques calculées par concurrent :
        - Score SEO global
        - Niveau de suroptimisation détaillé avec seuils basés sur la concurrence
        - Analyse des densités de mots-clés (normes du marché)
        - Patterns de keyword stuffing détectés
        - Recommandations d'optimisation adaptatives
        """
        # ÉTAPE 1: Collecte des données pour établir les normes du marché
        # Combinaison des mots-clés pour compatibilité avec l'ancienne méthode
        keywords = keywords_obligatoires + keywords_complementaires
        market_data = self._analyze_market_norms(serp_results, keywords)
        
        competitors = []
        keyword_dict = {kw[0]: kw[1] for kw in keywords}
        
        for result in serp_results:
            if not result.get("url"):
                continue
                
            # Contenu complet pour analyse
            full_content = " ".join([
                result.get("title", ""),
                result.get("h1", ""),
                result.get("h2", ""),
                result.get("h3", ""),
                result.get("content", ""),
                result.get("snippet", "")
            ])

            # 🔍 Vérification : contenu suffisant pour analyse
            content_words = self._tokenize_and_filter(full_content)
            has_sufficient_content = len(content_words) >= 50  # Minimum 50 mots

            # Calculs principaux avec seuils adaptatifs
            score = self._calculate_seo_score(full_content, keywords_obligatoires, keywords_complementaires)

            # ⚠️ Suroptimisation = 0 si contenu insuffisant (évite faux positifs)
            if has_sufficient_content:
                suroptimisation = self._calculate_adaptive_overoptimization(full_content, keywords, market_data)
                overopt_details = self._analyze_competitor_overoptimization_adaptive(full_content, keywords, market_data)
            else:
                suroptimisation = 0
                overopt_details = {"total_density": 0, "stuffing_count": 0, "clustering_penalty": 0, "flagged_keywords": []}
            
            competitor = {
                "h1": result.get("h1", ""),
                "title": result.get("title", ""),
                "h2": result.get("h2", ""),
                "h3": result.get("h3", ""),
                "score": score,
                "suroptimisation": suroptimisation,
                "position": result.get("position", 0),
                "words": result.get("word_count", 0),
                "url": result.get("url", ""),
                "domaine": result.get("domain", ""),
                "internal_links": result.get("internal_links", 0),
                "external_links": result.get("external_links", 0),
                "tableaux": result.get("tables", 0),
                "titles": result.get("titles", 0),
                "video": result.get("videos", 0),
                "liste": result.get("lists", 0),
                "image": result.get("images", 0),
                
                # 🆕 NOUVELLES MÉTRIQUES DE SUROPTIMISATION ADAPTATIVES
                "overopt_details": overopt_details,
                "keyword_density_total": overopt_details.get("total_density", 0),
                "stuffing_patterns": overopt_details.get("stuffing_count", 0),
                "clustering_issues": overopt_details.get("clustering_penalty", 0),
                "overopt_level": suroptimisation,
                "recommendations": self._generate_adaptive_optimization_recommendations(overopt_details, market_data)
            }
            
            competitors.append(competitor)
        
        # Tri par position pour faciliter l'analyse
        competitors.sort(key=lambda x: x.get("position", 999))
        
        return competitors
    
    def _analyze_market_norms(self, serp_results: List[Dict[str, Any]], keywords: List[List[Any]]) -> Dict[str, Any]:
        """
        📊 ANALYSE DES NORMES DU MARCHÉ POUR ÉTABLIR DES SEUILS ADAPTATIFS
        
        Collecte et analyse les densités/fréquences de tous les concurrents
        pour établir des seuils réalistes basés sur les données réelles.
        """
        market_densities = {}  # {keyword: [density1, density2, ...]}
        market_frequencies = {}  # {keyword: [freq1, freq2, ...]}
        total_densities = []  # Densités totales de chaque concurrent
        
        for result in serp_results:
            if not result.get("url"):
                continue
                
            full_content = " ".join([
                result.get("title", ""),
                result.get("h1", ""),
                result.get("h2", ""),
                result.get("h3", ""),
                result.get("content", ""),
                result.get("snippet", "")
            ])
            
            if not full_content.strip():
                continue
                
            content_words = self._tokenize_and_filter(full_content)
            word_counts = Counter(content_words)
            total_words = len(content_words)
            
            if total_words == 0:
                continue
            
            competitor_total_density = 0
            
            # Analyse des 15 mots-clés principaux
            for keyword_info in keywords[:15]:
                keyword = keyword_info[0].lower()
                frequency = word_counts.get(keyword, 0)
                density = (frequency / total_words) * 100 if frequency > 0 else 0
                
                if keyword not in market_densities:
                    market_densities[keyword] = []
                    market_frequencies[keyword] = []
                
                market_densities[keyword].append(density)
                market_frequencies[keyword].append(frequency)
                competitor_total_density += density
            
            total_densities.append(competitor_total_density)
        
        # Calcul des seuils adaptatifs basés sur les percentiles
        adaptive_thresholds = {}
        
        for keyword in market_densities:
            densities = [d for d in market_densities[keyword] if d > 0]
            frequencies = [f for f in market_frequencies[keyword] if f > 0]
            
            if densities:
                # Tri pour calculs de percentiles et médiane
                sorted_densities = sorted(densities)
                sorted_frequencies = sorted(frequencies)
                
                # Calculs de base
                mean_density = sum(densities) / len(densities)
                min_density = min(densities) 
                max_density = max(densities)
                median_density = sorted_densities[len(sorted_densities) // 2]
                
                mean_frequency = sum(frequencies) / len(frequencies)
                min_frequency = min(frequencies)
                max_frequency = max(frequencies)
                median_frequency = sorted_frequencies[len(sorted_frequencies) // 2]
                
                # Percentiles pour rétrocompatibilité
                p75_density = sorted_densities[int(len(sorted_densities) * 0.75)] if len(sorted_densities) > 3 else max_density
                p90_density = sorted_densities[int(len(sorted_densities) * 0.90)] if len(sorted_densities) > 9 else max_density
                p75_frequency = sorted_frequencies[int(len(sorted_frequencies) * 0.75)] if len(sorted_frequencies) > 3 else max_frequency
                p90_frequency = sorted_frequencies[int(len(sorted_frequencies) * 0.90)] if len(sorted_frequencies) > 9 else max_frequency
                
                adaptive_thresholds[keyword] = {
                    # Anciennes métriques pour rétrocompatibilité
                    'density_moderate': max(p75_density * 1.3, mean_density + 1.0),
                    'density_high': max(p90_density * 1.2, mean_density + 2.0),
                    'density_critical': max(max_density * 1.1, mean_density + 3.0),
                    'frequency_moderate': max(p75_frequency * 1.5, mean_frequency + 5),
                    'frequency_high': max(p90_frequency * 1.3, mean_frequency + 10),
                    'frequency_critical': max(max_frequency * 1.2, mean_frequency + 15),
                    
                    # Nouvelles métriques pour le système basé sur la médiane
                    'market_min_density': min_density,
                    'market_max_density': max_density,
                    'market_median_density': median_density,
                    'market_mean_density': mean_density,
                    'market_min_frequency': min_frequency,
                    'market_max_frequency': max_frequency,
                    'market_median_frequency': median_frequency,
                    'market_mean_frequency': mean_frequency
                }
        
        # Seuils pour la densité totale
        if total_densities:
            mean_total = sum(total_densities) / len(total_densities)
            max_total = max(total_densities)
            p75_total = sorted(total_densities)[int(len(total_densities) * 0.75)] if len(total_densities) > 3 else max_total
            p90_total = sorted(total_densities)[int(len(total_densities) * 0.90)] if len(total_densities) > 9 else max_total
            
            total_thresholds = {
                'moderate': max(p75_total * 1.4, mean_total + 5),
                'high': max(p90_total * 1.3, mean_total + 8),
                'critical': max(max_total * 1.2, mean_total + 12),
                'market_mean': mean_total,
                'market_max': max_total
            }
        else:
            # Fallback si pas de données
            total_thresholds = {
                'moderate': 20, 'high': 30, 'critical': 40,
                'market_mean': 10, 'market_max': 25
            }
        
        return {
            'keyword_thresholds': adaptive_thresholds,
            'total_density_thresholds': total_thresholds,
            'competitors_analyzed': len([r for r in serp_results if r.get("url")])
        }
    
    def _analyze_competitor_overoptimization(self, content: str, keywords: List[List[Any]]) -> Dict[str, Any]:
        """Analyse détaillée de la suroptimisation d'un concurrent"""
        if not content:
            return {"total_density": 0, "stuffing_count": 0, "clustering_penalty": 0, "flagged_keywords": []}
        
        content_words = self._tokenize_and_filter(content)
        content_lower = content.lower()
        word_counts = Counter(content_words)
        total_words = len(content_words)
        
        if total_words == 0:
            return {"total_density": 0, "stuffing_count": 0, "clustering_penalty": 0, "flagged_keywords": []}
        
        total_density = 0
        flagged_keywords = []
        stuffing_count = 0
        total_clustering_penalty = 0
        
        # Analyse de chaque mot-clé top 10
        for keyword_info in keywords[:10]:
            keyword = keyword_info[0].lower()
            frequency = word_counts.get(keyword, 0)
            
            if frequency == 0:
                continue
            
            density = (frequency / total_words) * 100
            total_density += density
            
            # Identifier les mots-clés problématiques
            keyword_analysis = {
                "keyword": keyword,
                "frequency": frequency,
                "density": round(density, 2),
                "issues": []
            }
            
            # Détection des problèmes - Seuils ajustés
            if density > 4.5:
                keyword_analysis["issues"].append("Densité critique (>4.5%)")
            elif density > 3.0:
                keyword_analysis["issues"].append("Densité élevée (>3.0%)")
            
            if frequency > 20:
                keyword_analysis["issues"].append("Fréquence excessive (>20)")
                stuffing_count += 1
            
            # Clustering
            positions = []
            start = 0
            while True:
                pos = content_lower.find(keyword, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
                
            if len(positions) >= 3:
                clustering_penalty = self._detect_keyword_clustering(positions, len(content))
                if clustering_penalty > 0:
                    keyword_analysis["issues"].append(f"Clustering détecté (pénalité: {clustering_penalty})")
                    total_clustering_penalty += clustering_penalty
            
            # Patterns de stuffing
            double_pattern = f"{keyword} {keyword}"
            if double_pattern in content_lower:
                keyword_analysis["issues"].append("Répétition immédiate détectée")
                stuffing_count += 1
            
            comma_pattern = f"{keyword},"
            if content_lower.count(comma_pattern) >= 2:
                keyword_analysis["issues"].append("Pattern de liste détecté")
                stuffing_count += 1
            
            if keyword_analysis["issues"]:
                flagged_keywords.append(keyword_analysis)
        
        return {
            "total_density": round(total_density, 2),
            "stuffing_count": stuffing_count,
            "clustering_penalty": total_clustering_penalty,
            "flagged_keywords": flagged_keywords,
            "content_length": total_words
        }
    
    def _analyze_competitor_overoptimization_adaptive(self, content: str, keywords: List[List[Any]], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse détaillée de la suroptimisation avec seuils adaptatifs basés sur la concurrence"""
        if not content:
            return {"total_density": 0, "stuffing_count": 0, "clustering_penalty": 0, "flagged_keywords": []}
        
        content_words = self._tokenize_and_filter(content)
        content_lower = content.lower()
        word_counts = Counter(content_words)
        total_words = len(content_words)
        
        if total_words == 0:
            return {"total_density": 0, "stuffing_count": 0, "clustering_penalty": 0, "flagged_keywords": []}
        
        total_density = 0
        flagged_keywords = []
        stuffing_count = 0
        total_clustering_penalty = 0
        keyword_thresholds = market_data.get('keyword_thresholds', {})
        
        # Analyse de chaque mot-clé avec seuils adaptatifs
        for keyword_info in keywords[:10]:
            keyword = keyword_info[0].lower()
            frequency = word_counts.get(keyword, 0)
            
            if frequency == 0:
                continue
            
            density = (frequency / total_words) * 100
            total_density += density
            
            # Récupération des seuils adaptatifs pour ce mot-clé
            thresholds = keyword_thresholds.get(keyword, {
                'density_moderate': 2.0, 'density_high': 3.0, 'density_critical': 4.5,
                'frequency_moderate': 15, 'frequency_high': 25, 'frequency_critical': 35
            })
            
            # Identifier les mots-clés problématiques avec seuils adaptatifs
            keyword_analysis = {
                "keyword": keyword,
                "frequency": frequency,
                "density": round(density, 2),
                "issues": [],
                "market_context": {
                    "mean_density": round(thresholds.get('market_mean_density', 0), 2),
                    "max_density": round(thresholds.get('market_max_density', 0), 2),
                    "mean_frequency": round(thresholds.get('market_mean_frequency', 0), 1),
                    "max_frequency": thresholds.get('market_max_frequency', 0)
                }
            }
            
            # Détection des problèmes avec seuils adaptatifs
            if density > thresholds['density_critical']:
                keyword_analysis["issues"].append(f"Densité critique (>{thresholds['density_critical']:.1f}% vs marché max: {thresholds.get('market_max_density', 0):.1f}%)")
            elif density > thresholds['density_high']:
                keyword_analysis["issues"].append(f"Densité élevée (>{thresholds['density_high']:.1f}% vs marché moy: {thresholds.get('market_mean_density', 0):.1f}%)")
            
            if frequency > thresholds['frequency_critical']:
                keyword_analysis["issues"].append(f"Fréquence critique (>{thresholds['frequency_critical']} vs marché max: {thresholds.get('market_max_frequency', 0)})")
                stuffing_count += 1
            elif frequency > thresholds['frequency_high']:
                keyword_analysis["issues"].append(f"Fréquence élevée (>{thresholds['frequency_high']} vs marché moy: {thresholds.get('market_mean_frequency', 0):.0f})")
            
            # Clustering (logique inchangée)
            positions = []
            start = 0
            while True:
                pos = content_lower.find(keyword, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
                
            if len(positions) >= 3:
                clustering_penalty = self._detect_keyword_clustering(positions, len(content))
                if clustering_penalty > 0:
                    keyword_analysis["issues"].append(f"Clustering détecté (pénalité: {clustering_penalty})")
                    total_clustering_penalty += clustering_penalty
            
            # Patterns de stuffing (logique inchangée)
            double_pattern = f"{keyword} {keyword}"
            if double_pattern in content_lower:
                keyword_analysis["issues"].append("Répétition immédiate détectée")
                stuffing_count += 1
            
            comma_pattern = f"{keyword},"
            if content_lower.count(comma_pattern) >= 2:
                keyword_analysis["issues"].append("Pattern de liste détecté")
                stuffing_count += 1
            
            if keyword_analysis["issues"]:
                flagged_keywords.append(keyword_analysis)
        
        return {
            "total_density": round(total_density, 2),
            "stuffing_count": stuffing_count,
            "clustering_penalty": total_clustering_penalty,
            "flagged_keywords": flagged_keywords,
            "content_length": total_words,
            "market_context": market_data.get('total_density_thresholds', {})
        }
    
    def _classify_overoptimization_level(self, score: int) -> str:
        """Classifie le niveau de suroptimisation avec des seuils simples"""
        if score >= 50:
            return "💀 Extrême"
        elif score >= 35:
            return "🚨 Critique"
        elif score >= 25:
            return "⚠️ Élevé"
        elif score >= 15:
            return "⚡ Modéré"
        elif score >= 8:
            return "📊 Faible"
        else:
            return "✅ Optimal"
    
    def _generate_optimization_recommendations(self, overopt_details: Dict[str, Any]) -> List[str]:
        """Génère des recommandations d'optimisation"""
        recommendations = []
        
        total_density = overopt_details.get("total_density", 0)
        stuffing_count = overopt_details.get("stuffing_count", 0)
        clustering_penalty = overopt_details.get("clustering_penalty", 0)
        flagged_keywords = overopt_details.get("flagged_keywords", [])
        
        if total_density > 25:
            recommendations.append("Réduire la densité totale des mots-clés (<18%)")
        
        if stuffing_count > 0:
            recommendations.append("Éliminer les patterns de keyword stuffing")
        
        if clustering_penalty > 15:
            recommendations.append("Distribuer les mots-clés plus naturellement")
        
        for kw in flagged_keywords:
            if kw["density"] > 4.5:
                recommendations.append(f"Réduire la densité de '{kw['keyword']}' (<3%)")
        
        if not recommendations:
            recommendations.append("Optimisation équilibrée - aucun problème majeur détecté")
        
        return recommendations
    
    def _calculate_adaptive_overoptimization(self, content: str, keywords: List[List[Any]], market_data: Dict[str, Any]) -> int:
        """
        Calcule le score de suroptimisation basé sur l'écart par rapport à la médiane du marché
        
        🎯 NOUVELLE APPROCHE :
        - Score 0 = Dans la norme (≤ médiane)
        - Score 1-50 = Au-dessus de la médiane, approche progressive
        - Score 51-100 = Spam évident, très au-dessus du maximum du marché
        """
        if not content:
            return 0
            
        content_words = self._tokenize_and_filter(content)
        word_counts = Counter(content_words)
        total_words = len(content_words)
        
        if total_words == 0:
            return 0
        
        total_score = 0
        keyword_thresholds = market_data.get('keyword_thresholds', {})
        
        # Analyse des 10 mots-clés principaux
        for keyword_info in keywords[:10]:
            keyword = keyword_info[0].lower()
            frequency = word_counts.get(keyword, 0)
            
            if frequency == 0:
                continue
                
            density = (frequency / total_words) * 100
            
            # Récupération des stats du marché pour ce mot-clé
            market_stats = keyword_thresholds.get(keyword, {})
            market_min_density = market_stats.get('market_min_density', 0)
            market_max_density = market_stats.get('market_max_density', 5)
            market_median_density = market_stats.get('market_median_density', 1)
            
            market_min_freq = market_stats.get('market_min_frequency', 0)
            market_max_freq = market_stats.get('market_max_frequency', 20)
            market_median_freq = market_stats.get('market_median_frequency', 3)
            
            # Score basé sur la densité
            if density > market_median_density:
                if density > market_max_density:
                    # Au-dessus du maximum du marché = spam évident
                    excess_ratio = (density - market_max_density) / max(market_max_density, 1)
                    density_score = min(50 + int(excess_ratio * 30), 70)  # 50-70 points
                else:
                    # Entre médiane et maximum = suroptimisation progressive
                    progress_ratio = (density - market_median_density) / max(market_max_density - market_median_density, 0.1)
                    density_score = int(progress_ratio * 30)  # 0-30 points
            else:
                density_score = 0  # Dans la norme
            
            # Score basé sur la fréquence
            if frequency > market_median_freq:
                if frequency > market_max_freq:
                    # Au-dessus du maximum du marché = spam évident
                    excess_ratio = (frequency - market_max_freq) / max(market_max_freq, 1)
                    freq_score = min(30 + int(excess_ratio * 20), 50)  # 30-50 points
                else:
                    # Entre médiane et maximum = suroptimisation progressive
                    progress_ratio = (frequency - market_median_freq) / max(market_max_freq - market_median_freq, 1)
                    freq_score = int(progress_ratio * 20)  # 0-20 points
            else:
                freq_score = 0  # Dans la norme
            
            # Score pour ce mot-clé (maximum des deux scores)
            keyword_score = max(density_score, freq_score)
            total_score += keyword_score
        
        # Limitation finale à 100 points maximum
        return min(total_score, 100)
    
    def _classify_adaptive_overoptimization_level(self, score: int, market_data: Dict[str, Any]) -> str:
        """Classifie le niveau de suroptimisation avec la nouvelle échelle 0-100"""
        # Nouvelle échelle basée sur la médiane du marché
        if score >= 80:
            return "💀 Extrême"  # Spam évident, très au-dessus du maximum
        elif score >= 60:
            return "🚨 Critique"  # Spam modéré, au-dessus du maximum
        elif score >= 40:
            return "⚠️ Élevé"     # Suroptimisation visible, près du maximum
        elif score >= 20:
            return "⚡ Modéré"     # Légèrement au-dessus de la médiane
        elif score >= 10:
            return "📊 Faible"     # Juste au-dessus de la médiane
        else:
            return "✅ Optimal"    # Dans la norme du marché (≤ médiane)
    
    def _generate_adaptive_optimization_recommendations(self, overopt_details: Dict[str, Any], market_data: Dict[str, Any]) -> List[str]:
        """Génère des recommandations d'optimisation adaptatives basées sur l'analyse concurrentielle"""
        recommendations = []
        
        total_density = overopt_details.get("total_density", 0)
        stuffing_count = overopt_details.get("stuffing_count", 0)
        clustering_penalty = overopt_details.get("clustering_penalty", 0)
        flagged_keywords = overopt_details.get("flagged_keywords", [])
        total_thresholds = market_data.get('total_density_thresholds', {})
        
        # Recommandations basées sur les normes du marché
        market_mean = total_thresholds.get('market_mean', 10)
        market_max = total_thresholds.get('market_max', 25)
        
        if total_density > total_thresholds.get('critical', 40):
            recommendations.append(f"Réduire drastiquement la densité totale (<{total_thresholds.get('high', 30):.0f}% - marché moy: {market_mean:.1f}%)")
        elif total_density > total_thresholds.get('high', 30):
            recommendations.append(f"Réduire la densité totale (<{total_thresholds.get('moderate', 20):.0f}% - marché moy: {market_mean:.1f}%)")
        
        if stuffing_count > 0:
            recommendations.append("Éliminer les patterns de keyword stuffing détectés")
        
        if clustering_penalty > 15:
            recommendations.append("Distribuer les mots-clés plus naturellement dans le texte")
        
        # Recommandations spécifiques par mot-clé avec contexte marché
        for kw in flagged_keywords[:3]:  # Limiter aux 3 plus problématiques
            market_context = kw.get("market_context", {})
            if kw["density"] > 4.0:
                target_density = min(market_context.get("mean_density", 2.0) * 1.5, 3.0)
                recommendations.append(f"'{kw['keyword']}': réduire à ~{target_density:.1f}% (marché: {market_context.get('mean_density', 0):.1f}%)")
        
        if not recommendations:
            if total_density < market_mean * 0.8:
                recommendations.append(f"Optimisation sous-exploitée - densité actuelle ({total_density:.1f}%) vs marché ({market_mean:.1f}%)")
            else:
                recommendations.append("Optimisation équilibrée selon les standards du marché")
        
        return recommendations
    
    def _detect_keyword_hybrid(self, content: str, keyword: str) -> int:
        """
        Détection hybride robuste avec fenêtre glissante + validation contextuelle
        
        🔍 MÉTHODE :
        1. Normalisation : suppression accents, ponctuation → espaces
        2. Fenêtre glissante pour expressions multi-mots
        3. Validation contextuelle pour cas complexes (apostrophes, tirets)
        """
        if not content or not keyword:
            return 0
        
        # Normalisation du contenu et du mot-clé
        normalized_content = self._normalize_for_detection(content)
        normalized_keyword = self._normalize_for_detection(keyword)
        
        # Tokenisation
        words = normalized_content.split()
        kw_parts = normalized_keyword.split()
        
        if not words or not kw_parts:
            return 0
        
        # === DÉTECTION PAR FENÊTRE GLISSANTE ===
        candidates_count = 0
        
        if len(kw_parts) == 1:
            # Mot simple : "créatine" → compte direct
            candidates_count = sum(1 for w in words if w == kw_parts[0])
        else:
            # Expression multi-mots : "créatine monohydrate" → fenêtre glissante
            k = len(kw_parts)
            for i in range(len(words) - k + 1):
                if all(words[i + j] == kw_parts[j] for j in range(k)):
                    candidates_count += 1
        
        # === VALIDATION CONTEXTUELLE ===
        # Activation pour cas complexes
        risky = ("'" in keyword) or ("-" in keyword) or (len(kw_parts) > 1)
        
        if risky and candidates_count > 0:
            # Pattern flexible pour variations typographiques (sur contenu normalisé)
            valid_count = self._validate_with_regex(normalized_content, normalized_keyword)
            # Sécurité : ne peut dépasser la détection normalisée
            return min(candidates_count, valid_count)
        
        return candidates_count
    
    def _normalize_for_detection(self, text: str) -> str:
        """Normalisation pour détection : accents + ponctuation → espaces"""
        import unicodedata
        
        # Suppression des accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        # Conversion en minuscules
        text = text.lower()
        
        # Ponctuation → espaces (garde apostrophes et tirets pour validation)
        import string
        punct_to_space = string.punctuation.replace("'", "").replace("-", "")
        for p in punct_to_space:
            text = text.replace(p, ' ')
        
        # Normalisation des espaces
        text = ' '.join(text.split())
        
        return text
    
    def _validate_with_regex(self, content: str, keyword: str) -> int:
        """Validation contextuelle avec pattern flexible"""
        import re
        
        # Division en parties
        parts = re.split(r"[''′\-\s]+", keyword.lower())
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            return 0
        
        # Séparateur flexible pour variations typographiques
        sep = r"(?:[''′\-\s]+)"
        
        # Construction du pattern core
        if len(parts) == 1:
            core = re.escape(parts[0])
        else:
            core = sep.join(re.escape(part) for part in parts)
        
        # Pattern avec boundaries pour éviter faux positifs
        pattern = rf"(?<![\w]){core}(?![\w])"
        
        # Recherche avec gestion d'erreurs
        try:
            matches = re.findall(pattern, content.lower(), re.IGNORECASE)
            return len(matches)
        except re.error:
            # Fallback si pattern invalide
            return 0
    
    def _calculate_seo_score(self, content: str, keywords_obligatoires: List, keywords_complementaires: List) -> int:
        """
        🎯 NOUVEAU CALCUL DE SCORE 70/30 avec détection hybride
        
        📊 MÉTHODE :
        - 70% pour les mots-clés obligatoires (réussis/total)
        - 30% pour les mots-clés complémentaires (réussis/total)
        - Malus de suroptimisation : (suroptimisés/total) × 20
        - Score final : max(0, min(100, base_score - malus))
        
        🔍 CRITÈRES :
        - Mot-clé "réussi" si freq_actuelle ≥ min_freq
        - Mot-clé "suroptimisé" si freq_actuelle > max_freq
        """
        if not content:
            return 0
        
        if not keywords_obligatoires and not keywords_complementaires:
            return 50  # Score neutre si pas de mots-clés
        
        # === COMPTAGE AVEC DÉTECTION HYBRIDE ===
        obligatoires_reussis = 0
        obligatoires_suroptimises = 0
        
        for kw_data in keywords_obligatoires:
            if len(kw_data) >= 5:  # [keyword, freq, importance, min_freq, max_freq]
                keyword = kw_data[0]
                min_freq = kw_data[3]
                max_freq = kw_data[4]
                
                # Détection hybride avec fenêtre glissante
                actual_freq = self._detect_keyword_hybrid(content, keyword)
                
                if actual_freq >= min_freq:
                    obligatoires_reussis += 1
                
                if actual_freq > max_freq:
                    obligatoires_suroptimises += 1
        
        complementaires_reussis = 0
        complementaires_suroptimises = 0
        
        for kw_data in keywords_complementaires:
            if len(kw_data) >= 5:  # [keyword, freq, importance, min_freq, max_freq]
                keyword = kw_data[0]
                min_freq = kw_data[3]
                max_freq = kw_data[4]
                
                # Détection hybride avec fenêtre glissante
                actual_freq = self._detect_keyword_hybrid(content, keyword)
                
                if actual_freq >= min_freq:
                    complementaires_reussis += 1
                
                if actual_freq > max_freq:
                    complementaires_suroptimises += 1
        
        # === CALCUL DU SCORE BASE ===
        total_obligatoires = len(keywords_obligatoires)
        total_complementaires = len(keywords_complementaires)
        
        # Score obligatoires (70%)
        if total_obligatoires > 0:
            score_obligatoires = (obligatoires_reussis / total_obligatoires) * 70
        else:
            score_obligatoires = 70  # Bonus si pas d'obligatoires
        
        # Score complémentaires (30%)
        if total_complementaires > 0:
            score_complementaires = (complementaires_reussis / total_complementaires) * 30
        else:
            score_complementaires = 30  # Bonus si pas de complémentaires
        
        base_score = score_obligatoires + score_complementaires
        
        # === MALUS DE SUROPTIMISATION ===
        total_mots_cles = total_obligatoires + total_complementaires
        total_suroptimises = obligatoires_suroptimises + complementaires_suroptimises
        
        if total_mots_cles > 0:
            malus = (total_suroptimises / total_mots_cles) * 20
        else:
            malus = 0
        
        # === SCORE FINAL ===
        score_final = max(0, min(100, base_score - malus))
        
        return int(score_final)
        
        # === SECTION 2: DIVERSITÉ SECONDAIRE (max 20 points) ===
        secondary_present = sum(1 for kw, _ in secondary_keywords if word_counts.get(kw, 0) > 0)
        # Bonus progressif pour la diversité
        if secondary_present >= 8:
            total_score += 20  # Excellente diversité
        elif secondary_present >= 6:
            total_score += 15  # Bonne diversité
        elif secondary_present >= 4:
            total_score += 10  # Diversité correcte
        elif secondary_present >= 2:
            total_score += 5   # Diversité faible
        
        # === SECTION 3: RICHESSE SÉMANTIQUE (max 15 points) ===
        tertiary_present = sum(1 for kw, _ in tertiary_keywords if word_counts.get(kw, 0) > 0)
        # Bonus pour le vocabulaire étendu
        if tertiary_present >= 10:
            total_score += 15  # Vocabulaire très riche
        elif tertiary_present >= 7:
            total_score += 10  # Vocabulaire riche
        elif tertiary_present >= 4:
            total_score += 5   # Vocabulaire correct
        
        # === SECTION 4: ÉQUILIBRE ET NATUREL (max 15 points) ===
        equilibrium_score = 0
        
        # Bonus pour distribution équilibrée des densités
        all_densities = []
        for keyword, _ in primary_keywords + secondary_keywords:
            freq = word_counts.get(keyword, 0)
            if freq > 0:
                density = (freq / total_words) * 100
                all_densities.append(density)
        
        if all_densities:
            # Coefficient de variation (écart-type / moyenne)
            mean_density = sum(all_densities) / len(all_densities)
            if mean_density > 0:
                variance = sum((d - mean_density) ** 2 for d in all_densities) / len(all_densities)
                cv = (variance ** 0.5) / mean_density
                
                # Bonus pour équilibre (coefficient de variation faible)
                if cv < 0.5:
                    equilibrium_score += 10  # Très équilibré
                elif cv < 1.0:
                    equilibrium_score += 6   # Équilibré
                elif cv < 1.5:
                    equilibrium_score += 3   # Modérément équilibré
        
        # Bonus pour longueur de contenu appropriée
        if 800 <= total_words <= 2500:
            equilibrium_score += 5  # Longueur optimale
        elif 400 <= total_words < 800 or 2500 < total_words <= 4000:
            equilibrium_score += 2  # Longueur acceptable
        
        total_score += min(equilibrium_score, 15)
        
        # === SECTION 5: PÉNALITÉS POUR SUROPTIMISATION ===
        # Pénalité pour mots-clés trop concentrés
        over_optimized_penalty = 0
        for keyword, _ in primary_keywords:
            freq = word_counts.get(keyword, 0)
            if freq > 0:
                density = (freq / total_words) * 100
                if density > 4.0:
                    over_optimized_penalty += min(int(density - 4.0) * 2, 10)
        
        total_score -= over_optimized_penalty
        
        # Score final entre 5 et 85 (jamais 0 ou 100)
        final_score = max(5, min(total_score, 85))
        
        return final_score
    
    # ANCIENNE FONCTION SUPPRIMÉE - Utilisez _calculate_adaptive_overoptimization à la place

    def _detect_keyword_clustering(self, positions: List[int], content_length: int) -> int:
        """Détecte les clusters anormaux de mots-clés rapprochés - Version ultra-réduite"""
        if len(positions) < 5:  # Seuil plus élevé : minimum 5 occurrences
            return 0
        
        penalty = 0
        window_size = max(300, content_length // 8)  # Fenêtre plus large
        
        for i in range(len(positions) - 4):  # Cherche 5+ occurrences minimum
            window_positions = [p for p in positions[i:] if p <= positions[i] + window_size]
            
            if len(window_positions) >= 5:  # 5+ occurrences dans la fenêtre
                penalty += 1  # Pénalité fixe ultra-réduite
                
        return min(penalty, 3)  # Plafond à 3 points maximum
    
    def _detect_keyword_stuffing_patterns(self, content: str, keywords: List[List[Any]]) -> int:
        """Détecte les patterns typiques de keyword stuffing - Version ultra-réduite"""
        penalty = 0
        
        # Pattern 1: Listes de mots-clés séparés par des virgules (plus strict)
        for keyword_info in keywords:
            keyword = keyword_info[0].lower()
            
            # Recherche de patterns comme "créatine, whey, protéine, masse"
            comma_pattern = f"{keyword}," 
            if content.count(comma_pattern) >= 3:  # Seuil plus élevé : 3+ occurrences
                penalty += 1  # Pénalité ultra-réduite
            
            # Pattern 2: Répétitions immédiates ("créatine créatine créatine")
            double_pattern = f"{keyword} {keyword}"
            if double_pattern in content:
                penalty += 1  # Pénalité ultra-réduite
            
            # Pattern 3: Seulement si vraiment excessif
            if content.count(keyword) >= 10:  # Seuil beaucoup plus élevé
                # Compte les occurrences dans un rayon de 100 caractères (plus large)
                start = 0
                while True:
                    pos = content.find(keyword, start)
                    if pos == -1:
                        break
                    
                    # Vérifie la zone autour pour d'autres occurrences
                    zone_start = max(0, pos - 100)  # Rayon plus large
                    zone_end = min(len(content), pos + len(keyword) + 100)
                    zone = content[zone_start:zone_end]
                    
                    zone_count = zone.count(keyword)
                    if zone_count >= 5:  # Seuil plus élevé
                        penalty += 1  # Pénalité ultra-réduite
                        break
                    
                    start = pos + 1
        
        return min(penalty, 5)  # Plafond à 5 points maximum
    
    def _calculate_target_score(self, competitors: List[Dict[str, Any]]) -> int:
        """
        Calcule le score cible recommandé basé sur l'analyse concurrentielle
        
        📊 MÉTHODE DE CALCUL DU SCORE CIBLE :
        
        1️⃣ COLLECTE DES DONNÉES
           - Récupère les scores SEO de tous les concurrents du top 10
           - Filtre les scores valides (> 0)
        
        2️⃣ ANALYSE COMPETITIVE
           - Sélectionne les 3 meilleurs scores (top performers)
           - Calcule la moyenne de ces scores d'excellence
        
        3️⃣ OBJECTIF STRATÉGIQUE 
           - Ajoute 10% à cette moyenne pour être compétitif
           - Assure de surpasser les leaders actuels
        
        4️⃣ VALIDATION
           - Plafonne à 100 points maximum
           - Score de base : 50 si pas de données
        
        💡 Le score SEO individuel est calculé selon :
        - Densité et présence des mots-clés obligatoires
        - Distribution sémantique naturelle
        - Optimisation technique du contenu
        """
        if not competitors:
            return 50
            
        scores = [comp.get("score", 0) for comp in competitors if comp.get("score", 0) > 0]
        if not scores:
            return 50
            
        # Score cible = moyenne des 5 premiers (au lieu de 3) pour TOP 20
        top_scores = sorted(scores, reverse=True)[:5]  # TOP 5 au lieu de TOP 3
        target = int(mean(top_scores) + 5)  # Ajout de 5 points au lieu de 10%
        return min(target, 95)  # Plafond plus réaliste à 95
    
    def _calculate_required_words(self, competitors: List[Dict[str, Any]]) -> int:
        """Calcule le nombre de mots recommandé avec une approche plus équilibrée"""
        if not competitors:
            return 800

        word_counts = [comp.get("words", 0) for comp in competitors if comp.get("words", 0) > 100]
        if not word_counts:
            return 800

        # Utiliser la médiane des TOP 8 (au lieu de tout) pour TOP 20
        word_counts_sorted = sorted(word_counts, reverse=True)[:8]  # TOP 8
        median_words = sorted(word_counts_sorted)[len(word_counts_sorted)//2]

        # Cible = médiane + marge raisonnable (pas 10% mais +200 mots)
        target = median_words + 200

        # Limite minimale raisonnable de 600 mots
        return max(target, 600)
    
    def _calculate_max_overoptimization(self, keywords: List[List[Any]]) -> int:
        """Calcule le seuil maximum de suroptimisation acceptable"""
        if not keywords:
            return 5
            
        # Basé sur le nombre de mots-clés principaux
        main_keywords = len([kw for kw in keywords if kw[2] > 15])
        return max(3, min(main_keywords // 2, 8))
    
    def _analyze_content_types(self, serp_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyse les types de contenu dans les résultats"""
        editorial = 0
        catalogue = 0
        fiche_produit = 0
        
        for result in serp_results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            
            # Détection de fiches produits
            if any(term in url for term in ['/produit/', '/product/', 'acheter', 'prix', 'commander']):
                fiche_produit += 1
            # Détection de catalogues
            elif any(term in url for term in ['/categorie/', '/collection/', 'boutique', 'shop']):
                catalogue += 1
            # Contenu éditorial par défaut
            else:
                editorial += 1
        
        total = len(serp_results)
        return {
            "editorial": int((editorial / total) * 100) if total > 0 else 100,
            "catalogue": int((catalogue / total) * 100) if total > 0 else 0,
            "fiche_produit": int((fiche_produit / total) * 100) if total > 0 else 0
        }
    
    def _calculate_word_statistics(self, serp_results: List[Dict[str, Any]]) -> List[int]:
        """Calcule les statistiques de mots (min, max, moyenne)"""
        word_counts = [result.get("word_count", 0) for result in serp_results if result.get("word_count", 0) > 0]
        
        if not word_counts:
            return [800, 1500, 1200]
        
        return [min(word_counts), max(word_counts), int(mean(word_counts))]
    
    def _get_demo_analysis(self, query: str) -> Dict[str, Any]:
        """Retourne l'analyse de démonstration basée sur l'exemple fourni"""
        # Calculer un score cible variable selon la requête
        demo_competitors = [
            {"score": 72}, {"score": 64}, {"score": 58}, {"score": 45}, {"score": 38}
        ]
        calculated_target = self._calculate_target_score(demo_competitors)
        
        return {
            "query": query,
            "score_target": calculated_target,
            "mots_requis": 1100,
            "KW_obligatoires": [["créatine",2,44,3,8],["whey",1,35,2,6],["prise",1,33,1,4],["muscle",2,29,2,7],["complément",2,27,1,5],["masse",2,25,2,6],["bcaa",1,25,1,3],["protéine",5,20,3,12],["alimentaire",2,21,1,4],["musculaire",2,17,2,5],["effet",3,12,1,6],["récupération",1,14,1,3],["musculation",1,12,1,2],["produit",1,12,1,3],["acide",2,10,1,4],["aminé",2,10,1,4],["force",2,9,1,4],["énergie",1,11,1,2],["monohydrate",2,8,1,4],["poudre",2,9,1,4],["dose",1,8,1,2],["consommer",1,8,1,2],["effort",2,9,1,4],["jour",1,8,1,2],["shaker",1,7,1,2],["objectif",1,7,1,2],["source",1,7,1,2],["séance",2,7,1,4],["sport",1,6,1,2],["lait",1,5,1,2],["sportif",1,6,1,2],["endurance",1,5,1,2],["exemple",1,5,1,2],["étude",1,5,1,2],["corps",1,6,1,2],["consommation",1,5,1,2],["recommandée",2,4,1,4],["bienfait",1,5,1,2],["puissance",1,6,1,2],["apport",1,5,1,2],["graisse",1,6,1,2],["meilleure",1,3,1,2],["haute",1,4,1,2],["santé",2,3,1,4],["rôle",1,4,1,2]],
            "KW_complementaires": [["pack",2,33,1,4],["collation",2,17,1,3],["taux",5,9,2,8],["substance",2,10,1,3],["point",1,11,1,2],["marque",4,6,2,6],["augmenter",2,8,1,3],["personne",1,8,1,2],["amélioration",1,8,1,2],["utilisé",1,8,1,2],["matin",2,8,1,3],["midi",2,8,1,3],["performance",2,7,1,3],["booster",1,7,1,2],["meilleur",1,7,1,2],["sportive",1,7,1,2],["développement",2,5,1,3],["prix",4,5,2,6],["gamme",1,7,1,2],["forme",2,6,1,3],["intense",2,7,1,3],["organisme",1,7,1,2],["court",2,7,1,3],["qualité",1,7,1,2],["profiter",1,7,1,2],["risque",1,7,1,2],["composition",2,7,1,3],["fabriqué",2,5,1,3],["choisir",2,4,1,3],["associer",2,4,1,3],["nutrition",2,4,1,3],["croissance",1,5,1,2],["isolate",1,4,1,2],["training",2,3,1,3],["eau",2,4,1,3],["bénéfique",1,5,1,2]],
            "ngrams": [
                ["créatine monohydrate pour prise masse", 4, 85],
                ["différence entre créatine et whey", 3, 82],
                ["comment prendre créatine et whey", 3, 78],
                ["meilleur moment prendre créatine", 2, 65],
                ["supplémentation en créatine et protéine", 2, 62],
                ["effet de la créatine sur", 4, 58],
                ["phase de charge créatine nécessaire", 2, 55],
                ["whey protein isolate native qualité", 2, 52],
                ["récupération musculaire après entraînement intensif", 2, 50],
                ["synthèse des protéines musculaires", 3, 48],
                ["développement de la masse musculaire", 2, 45],
                ["adénosine triphosphate et performance sportive", 2, 42],
                ["acides aminés essentiels pour muscle", 2, 40],
                ["nutrition sportive optimale pour gains", 2, 38],
                ["complément alimentaire naturel sans danger", 2, 35],
                ["force et puissance musculaire explosive", 2, 32],
                ["construction musculaire rapide et efficace", 2, 30],
                ["régime alimentaire équilibré pour sportif", 2, 28],
                ["amélioration des performances en musculation", 2, 25],
                ["prise de poids masse maigre", 2, 22]
            ],
            "max_suroptimisation": 5,
            "questions": "Quel est le mieux entre la créatine et la whey ?;Est-ce qu'on peut mélanger la créatine et la whey ?;Quelle est la différence entre la créatine et la protéine ?;Est-ce que la créatine fait prendre du muscle ?;Est-ce qu'on peut mélanger créatine et whey ?;Quand prendre son shaker de whey et de créatine ?;Comment prendre de la créatine et de la whey ?;Comment prendre protéine et créatine ?;Quand prendre la protéine et la créatine ?;Quel est le mieux entre créatine et protéine ?;Est-ce que la créatine est une protéine ?;Est-ce que on peut mélanger la créatine avec la protéine ?;Est-ce bon de prendre de la créatine ?;Est-ce que la créatine augmente la masse musculaire ?;Quand voit-on les effets de la créatine ?;Quels sont les effets positifs de la créatine ?;Qu'est-ce que la créatine ? ;La prise de créatine est-elle efficace ? ;Faut-il prendre la whey et la créatine en même temps ? ;Faut-il nécessairement consommer un mélange de whey et de créatine ?",
            "paa": [
                "Quel est le mieux entre la créatine et la whey ?",
                "Est-ce qu'on peut mélanger la créatine et la whey ?", 
                "Quelle est la différence entre la créatine et la protéine ?",
                "Comment prendre de la créatine et de la whey ?",
                "Quand prendre la protéine et la créatine ?",
                "Est-ce que la créatine fait prendre du muscle ?"
            ],
            "related_searches": [],
            "inline_videos": [],
            "bigrams": [
                ["créatine monohydrate", 8, 31],
                ["prise masse", 6, 27],
                ["whey protein", 5, 25],
                ["masse musculaire", 7, 24],
                ["complément alimentaire", 4, 23],
                ["récupération musculaire", 3, 21],
                ["force musculaire", 4, 18],
                ["protéine whey", 4, 16],
                ["acide aminé", 3, 15],
                ["développement musculaire", 2, 14],
                ["nutrition sportive", 3, 13],
                ["synthèse protéines", 2, 12],
                ["performance sportive", 2, 11],
                ["musculation intensive", 2, 10],
                ["shaker protéine", 2, 9],
                ["entraînement intensif", 3, 8],
                ["croissance musculaire", 2, 8],
                ["endurance physique", 2, 7]
            ],
            "trigrams": [
                ["créatine prise masse", 4, 32],
                ["whey créatine bcaa", 3, 28],
                ["complément alimentaire musculation", 3, 25],
                ["masse musculaire rapidement", 2, 22],
                ["récupération musculaire optimale", 2, 20],
                ["protéine whey isolate", 3, 18],
                ["créatine monohydrate pure", 2, 17],
                ["force puissance musculaire", 2, 15],
                ["développement masse maigre", 2, 14],
                ["nutrition sportive avancée", 2, 13]
            ],
            "type_editorial": 100,
            "type_catalogue": 0,
            "type_fiche_produit": 0,
            "mots_uniques_min_max_moyenne": [37, 57, 49],
            "concurrence": [
                {
                    "h1": "Créatine vs Whey : Le Guide Complet 2024",
                    "title": "Créatine ou Whey : Que Choisir pour Maximiser ses Gains ?",
                    "h2": "Comparaison scientifique créatine et whey",
                    "h3": "Effets sur la masse musculaire",
                    "score": 72,
                    "suroptimisation": 3,
                    "position": 1,
                    "words": 1250,
                    "url": "https://www.nutrimuscle.com/creatine-vs-whey-guide",
                    "domaine": "nutrimuscle.com",
                    "internal_links": 8,
                    "external_links": 2,
                    "tableaux": 1,
                    "titles": 6,
                    "video": 1,
                    "liste": 3,
                    "image": 12,
                    "overopt_details": {"total_density": 4.2, "stuffing_count": 0, "clustering_penalty": 0, "flagged_keywords": []},
                    "keyword_density_total": 4.2,
                    "stuffing_patterns": 0,
                    "clustering_issues": 0,
                    "overopt_level": "📊 Faible",
                    "recommendations": ["Optimisation équilibrée - aucun problème majeur détecté"]
                },
                {
                    "h1": "Quels sont les bienfaits de la créatine sur la prise de masse ?",
                    "title": "Créatine et prise de masse : à quoi s'attendre réellement ?",
                    "h2": "Comment prendre de la créatine pour faire une prise de masse ?",
                    "h3": "Quand prendre de la créatine pour une prise de masse ?",
                    "score": 64,
                    "suroptimisation": 8,
                    "position": 2,
                    "words": 1075,
                    "url": "https://nutriandco.com/fr/pages/creatine-prise-de-masse",
                    "domaine": "nutriandco.com",
                    "internal_links": 12,
                    "external_links": 0,
                    "tableaux": 0,
                    "titles": 8,
                    "video": 0,
                    "liste": 2,
                    "image": 54,
                    "overopt_details": {"total_density": 6.8, "stuffing_count": 0, "clustering_penalty": 2, "flagged_keywords": []},
                    "keyword_density_total": 6.8,
                    "stuffing_patterns": 0,
                    "clustering_issues": 2,
                    "overopt_level": "📊 Faible",
                    "recommendations": ["Optimisation équilibrée - aucun problème majeur détecté"]
                },
                {
                    "h1": "Whey ou Créatine : Quel Complément Choisir ?",
                    "title": "Whey vs Créatine : Différences et Conseils d'Utilisation",
                    "h2": "Les avantages de la whey protéine",
                    "h3": "Les bénéfices de la créatine monohydrate",
                    "score": 58,
                    "suroptimisation": 12,
                    "position": 3,
                    "words": 890,
                    "url": "https://www.myprotein.fr/blog/supplements/whey-vs-creatine",
                    "domaine": "myprotein.fr",
                    "internal_links": 15,
                    "external_links": 1,
                    "tableaux": 2,
                    "titles": 7,
                    "video": 0,
                    "liste": 4,
                    "image": 8,
                    "overopt_details": {"total_density": 9.1, "stuffing_count": 1, "clustering_penalty": 3, "flagged_keywords": []},
                    "keyword_density_total": 9.1,
                    "stuffing_patterns": 1,
                    "clustering_issues": 3,
                    "overopt_level": "📊 Faible",
                    "recommendations": ["Distribuer les mots-clés plus naturellement"]
                },
                {
                    "h1": "Guide Complet : Créatine et Whey pour la Musculation",
                    "title": "Créatine + Whey : La Combinaison Parfaite ?",
                    "h2": "Peut-on mélanger créatine et whey ?",
                    "h3": "Dosage optimal créatine et protéines",
                    "score": 45,
                    "suroptimisation": 15,
                    "position": 4,
                    "words": 1420,
                    "url": "https://www.bodybuilding.fr/creatine-whey-guide",
                    "domaine": "bodybuilding.fr",
                    "internal_links": 6,
                    "external_links": 3,
                    "tableaux": 1,
                    "titles": 9,
                    "video": 2,
                    "liste": 1,
                    "image": 18,
                    "overopt_details": {"total_density": 11.4, "stuffing_count": 2, "clustering_penalty": 5, "flagged_keywords": [{"keyword": "créatine", "frequency": 8, "density": 2.8, "issues": ["Densité élevée (>2.2%)"]}]},
                    "keyword_density_total": 11.4,
                    "stuffing_patterns": 2,
                    "clustering_issues": 5,
                    "overopt_level": "📊 Faible",
                    "recommendations": ["Distribuer les mots-clés plus naturellement", "Éliminer les patterns de keyword stuffing"]
                },
                {
                    "h1": "Créatine ou Protéine : Que Prendre en Premier ?",
                    "title": "Créatine vs Protéine : Guide du Débutant 2024",
                    "h2": "Différences entre créatine et whey protein",
                    "h3": "Quel budget pour ces compléments ?",
                    "score": 38,
                    "suroptimisation": 22,
                    "position": 5,
                    "words": 756,
                    "url": "https://musculation.ooreka.fr/astuce/voir/735543/creatine-ou-proteine",
                    "domaine": "musculation.ooreka.fr",
                    "internal_links": 3,
                    "external_links": 0,
                    "tableaux": 0,
                    "titles": 4,
                    "video": 0,
                    "liste": 1,
                    "image": 6,
                    "overopt_details": {"total_density": 15.2, "stuffing_count": 3, "clustering_penalty": 8, "flagged_keywords": [{"keyword": "créatine", "frequency": 12, "density": 3.8, "issues": ["Densité critique (>3.5%)", "Fréquence excessive (>12)"]}, {"keyword": "protéine", "frequency": 9, "density": 2.4, "issues": ["Densité élevée (>2.2%)"]}]},
                    "keyword_density_total": 15.2,
                    "stuffing_patterns": 3,
                    "clustering_issues": 8,
                    "overopt_level": "⚡ Modéré",
                    "recommendations": ["Réduire la densité de 'créatine' (<2%)", "Réduire la densité de 'protéine' (<2%)", "Distribuer les mots-clés plus naturellement", "Éliminer les patterns de keyword stuffing"]
                }
            ]
        }
    
    async def _enhance_keywords_with_llm(self, keywords: List[List[Any]], query: str, keyword_type: str) -> List[List[Any]]:
        """
        🤖 Améliore la qualité des mots-clés via filtrage LLM (optionnel)
        
        Args:
            keywords: Liste des mots-clés [mot, fréquence, importance, ...]
            query: Requête SEO originale
            keyword_type: "required" ou "complementary" pour logging
            
        Returns:
            Liste filtrée des mots-clés (sans parasites)
        """
        
        print(f"🔍 _enhance_keywords_with_llm appelé pour {keyword_type}, {len(keywords)} mots-clés")
        print(f"🔍 self.llm_filter: {self.llm_filter}")
        print(f"🔍 self.llm_filter.enabled: {self.llm_filter.enabled if self.llm_filter else 'None'}")
        
        # Si service LLM non disponible, retourner les mots-clés originaux
        if not self.llm_filter or not self.llm_filter.enabled:
            print(f"⚠️ LLM Service non disponible pour {keyword_type}, retour mots-clés originaux")
            return keywords
        
        try:
            # Extraction des mots-clés seuls (première colonne)
            keywords_only = [kw[0] for kw in keywords if len(kw) > 0]
            
            if not keywords_only:
                return keywords
            
            # Filtrage via LLM
            filtered_keywords = await self.llm_filter.filter_keywords_batch(keywords_only, query)
            
            # Reconstruction des tuples avec métadonnées pour les mots-clés conservés
            enhanced_keywords = []
            for original_kw in keywords:
                if len(original_kw) > 0 and original_kw[0].lower() in [fkw.lower() for fkw in filtered_keywords]:
                    enhanced_keywords.append(original_kw)
            
            # Logging des améliorations
            removed_count = len(keywords) - len(enhanced_keywords)
            if removed_count > 0:
                print(f"🤖 LLM amélioration {keyword_type}: {removed_count} mots-clés parasites supprimés")
            
            return enhanced_keywords
            
        except Exception as e:
            # Fallback silencieux vers mots-clés originaux
            print(f"⚠️ LLM fallback pour {keyword_type}: {str(e)}")
            return keywords 