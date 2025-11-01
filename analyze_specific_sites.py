#!/usr/bin/env python3
"""
Analyse détaillée des mots détectés sur sites spécifiques
"""

import asyncio
from services.valueserp_service import ValueSerpService
from collections import Counter
import re
from typing import Dict, List, Tuple
import nltk
from nltk.corpus import stopwords

class SpecificSiteAnalyzer:
    def __init__(self):
        self.service = ValueSerpService()
        
        # Stop words français étendus
        try:
            self.french_stopwords = set(stopwords.words('french'))
        except:
            nltk.download('stopwords')
            self.french_stopwords = set(stopwords.words('french'))
        
        # Ajout de stop words SEO spécifiques
        self.french_stopwords.update([
            'a', 'à', 'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'ce', 'cette',
            'et', 'ou', 'mais', 'car', 'donc', 'or', 'ni', 'que', 'qui', 'dont', 'où',
            'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'on', 'se', 'sa', 'son', 'ses',
            'pour', 'par', 'avec', 'sans', 'dans', 'sur', 'sous', 'vers', 'entre', 'chez',
            'plus', 'moins', 'très', 'bien', 'mal', 'mieux', 'beaucoup', 'peu', 'assez',
            'tout', 'tous', 'toute', 'toutes', 'autre', 'autres', 'même', 'mêmes',
            'avoir', 'être', 'faire', 'dire', 'aller', 'voir', 'savoir', 'pouvoir',
            'depuis', 'pendant', 'après', 'avant', 'encore', 'déjà', 'toujours', 'jamais'
        ])
    
    async def extract_and_analyze(self, url: str) -> Dict:
        """Extrait et analyse le contenu d'un site"""
        print(f"🔍 Analyse de: {url}")
        print("=" * 60)
        
        try:
            # Extraction avec trafilatura
            result = await self.service._fetch_page_content(url)
            
            if result['word_count'] == 0:
                return {
                    'url': url,
                    'status': 'failed',
                    'error': 'Aucun contenu extrait'
                }
            
            content = result['content']
            
            print(f"✅ Extraction réussie:")
            print(f"   - Mots total: {result['word_count']}")
            print(f"   - Qualité: {result['content_quality']}")
            print(f"   - H1: {result.get('h1', 'N/A')}")
            print(f"   - Auteur: {result.get('author', 'N/A')}")
            print(f"   - Date: {result.get('date', 'N/A')}")
            
            # Analyse des mots
            analysis = self._analyze_words(content)
            analysis.update({
                'url': url,
                'total_words': result['word_count'],
                'quality': result['content_quality'],
                'metadata': {
                    'h1': result.get('h1', ''),
                    'author': result.get('author', ''),
                    'date': result.get('date', ''),
                    'description': result.get('description', '')
                },
                'html_stats': {
                    'images': result['images'],
                    'internal_links': result['internal_links'],
                    'external_links': result['external_links'],
                    'tables': result['tables'],
                    'lists': result['lists']
                }
            })
            
            return analysis
            
        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_words(self, content: str) -> Dict:
        """Analyse détaillée des mots du contenu"""
        
        # Nettoyage du texte
        clean_text = self._clean_text(content)
        words = clean_text.split()
        
        # Filtrage des stop words
        meaningful_words = [
            word for word in words 
            if word.lower() not in self.french_stopwords 
            and len(word) >= 3
            and not word.isdigit()
        ]
        
        # Comptage des mots
        word_freq = Counter(meaningful_words)
        
        # Extraction des expressions (bi-grammes et tri-grammes)
        bigrams = self._extract_bigrams(words)
        trigrams = self._extract_trigrams(words)
        
        return {
            'raw_word_count': len(words),
            'meaningful_word_count': len(meaningful_words),
            'unique_words': len(set(meaningful_words)),
            'vocabulary_richness': len(set(meaningful_words)) / len(meaningful_words) if meaningful_words else 0,
            'top_words': word_freq.most_common(20),
            'top_bigrams': bigrams,
            'top_trigrams': trigrams,
            'word_categories': self._categorize_words(meaningful_words),
            'content_preview': content[:300] + "..." if len(content) > 300 else content
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour l'analyse"""
        # Supprime la ponctuation excessive
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        # Normalise les espaces
        text = re.sub(r'\s+', ' ', text)
        # Supprime les mots trop courts ou trop longs
        words = [word for word in text.split() if 2 <= len(word) <= 50]
        return ' '.join(words)
    
    def _extract_bigrams(self, words: List[str]) -> List[Tuple[str, int]]:
        """Extrait les bi-grammes significatifs"""
        bigrams = []
        for i in range(len(words) - 1):
            word1, word2 = words[i].lower(), words[i+1].lower()
            
            # Filtre les bi-grammes avec stop words
            if (word1 not in self.french_stopwords and 
                word2 not in self.french_stopwords and
                len(word1) >= 3 and len(word2) >= 3):
                bigrams.append(f"{word1} {word2}")
        
        return Counter(bigrams).most_common(10)
    
    def _extract_trigrams(self, words: List[str]) -> List[Tuple[str, int]]:
        """Extrait les tri-grammes significatifs"""
        trigrams = []
        for i in range(len(words) - 2):
            word1, word2, word3 = words[i].lower(), words[i+1].lower(), words[i+2].lower()
            
            # Au moins 2 mots non-stop words dans le tri-gramme
            non_stop_count = sum(1 for w in [word1, word2, word3] if w not in self.french_stopwords)
            
            if non_stop_count >= 2 and all(len(w) >= 3 for w in [word1, word2, word3]):
                trigrams.append(f"{word1} {word2} {word3}")
        
        return Counter(trigrams).most_common(8)
    
    def _categorize_words(self, words: List[str]) -> Dict[str, List[str]]:
        """Catégorise les mots par thème"""
        
        categories = {
            'technique': [],
            'business': [],
            'action': [],
            'qualité': [],
            'service': [],
            'autres': []
        }
        
        # Dictionnaires de catégorisation
        tech_words = {'web', 'site', 'digital', 'seo', 'marketing', 'développement', 'création', 'design', 'responsive', 'mobile'}
        business_words = {'entreprise', 'société', 'client', 'service', 'projet', 'équipe', 'expertise', 'expérience', 'solution', 'accompagnement'}
        action_words = {'créer', 'développer', 'concevoir', 'réaliser', 'optimiser', 'améliorer', 'proposer', 'offrir', 'accompagner', 'conseiller'}
        quality_words = {'qualité', 'professionnel', 'expert', 'spécialisé', 'performant', 'efficace', 'optimal', 'personnalisé', 'sur-mesure'}
        
        for word in words[:100]:  # Limite pour performance
            word_lower = word.lower()
            
            if word_lower in tech_words:
                categories['technique'].append(word)
            elif word_lower in business_words:
                categories['business'].append(word)
            elif word_lower in action_words:
                categories['action'].append(word)
            elif word_lower in quality_words:
                categories['qualité'].append(word)
            elif any(service_word in word_lower for service_word in ['service', 'prestation', 'offre']):
                categories['service'].append(word)
            else:
                if len(categories['autres']) < 20:  # Limite les "autres"
                    categories['autres'].append(word)
        
        return categories
    
    def _display_analysis(self, analysis: Dict):
        """Affiche l'analyse de manière structurée"""
        
        if analysis.get('status') in ['failed', 'error']:
            print(f"❌ Échec: {analysis['error']}")
            return
        
        print(f"\n📊 STATISTIQUES MOTS:")
        print(f"   - Mots bruts: {analysis['raw_word_count']}")
        print(f"   - Mots significatifs: {analysis['meaningful_word_count']}")
        print(f"   - Mots uniques: {analysis['unique_words']}")
        print(f"   - Richesse vocabulaire: {analysis['vocabulary_richness']:.2f}")
        
        print(f"\n🔝 TOP 20 MOTS SIGNIFICATIFS:")
        for i, (word, count) in enumerate(analysis['top_words'], 1):
            print(f"   {i:2}. {word:<20} ({count}x)")
        
        print(f"\n🔗 TOP EXPRESSIONS (BI-GRAMMES):")
        for i, (bigram, count) in enumerate(analysis['top_bigrams'], 1):
            print(f"   {i}. \"{bigram}\" ({count}x)")
        
        print(f"\n📝 TOP EXPRESSIONS (TRI-GRAMMES):")
        for i, (trigram, count) in enumerate(analysis['top_trigrams'], 1):
            print(f"   {i}. \"{trigram}\" ({count}x)")
        
        print(f"\n🏷️ CATÉGORISATION DES MOTS:")
        for category, words in analysis['word_categories'].items():
            if words:
                print(f"   {category.upper()}: {', '.join(words[:10])}")
        
        print(f"\n📄 APERÇU DU CONTENU:")
        print(f"   {analysis['content_preview']}")
        
        print(f"\n📈 STATISTIQUES HTML:")
        stats = analysis['html_stats']
        print(f"   - Images: {stats['images']}")
        print(f"   - Liens internes: {stats['internal_links']}")
        print(f"   - Liens externes: {stats['external_links']}")
        print(f"   - Tableaux: {stats['tables']}")
        print(f"   - Listes: {stats['lists']}")
    
    async def analyze_multiple_sites(self, urls: List[str]):
        """Analyse plusieurs sites"""
        
        print("🚀 ANALYSE DÉTAILLÉE DES SITES DEMANDÉS")
        print("=" * 80)
        
        analyses = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n\n🎯 SITE {i}/{len(urls)}")
            analysis = await self.extract_and_analyze(url)
            analyses.append(analysis)
            
            self._display_analysis(analysis)
        
        # Comparaison globale si plusieurs sites
        if len(analyses) > 1:
            self._compare_sites(analyses)
        
        return analyses
    
    def _compare_sites(self, analyses: List[Dict]):
        """Compare les analyses de plusieurs sites"""
        
        print(f"\n\n🆚 COMPARAISON GLOBALE")
        print("=" * 80)
        
        valid_analyses = [a for a in analyses if a.get('status') not in ['failed', 'error']]
        
        if len(valid_analyses) < 2:
            print("Pas assez de sites valides pour comparaison")
            return
        
        print("📊 COMPARATIF:")
        for analysis in valid_analyses:
            print(f"\n🌐 {analysis['url']}:")
            print(f"   - Mots total: {analysis['total_words']}")
            print(f"   - Mots significatifs: {analysis['meaningful_word_count']}")
            print(f"   - Vocabulaire unique: {analysis['unique_words']}")
            print(f"   - Qualité: {analysis['quality']}")
            print(f"   - Top mot: {analysis['top_words'][0][0] if analysis['top_words'] else 'N/A'}")
            print(f"   - Top expression: {analysis['top_bigrams'][0][0] if analysis['top_bigrams'] else 'N/A'}")

async def main():
    analyzer = SpecificSiteAnalyzer()
    
    urls = [
        "https://agence-slashr.fr/",
        "https://cuve-expert.fr/231-cuve-a-eau-2000l"
    ]
    
    await analyzer.analyze_multiple_sites(urls)

if __name__ == "__main__":
    asyncio.run(main())