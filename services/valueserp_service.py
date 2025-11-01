import httpx
import os
from typing import Dict, List, Any
import asyncio
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.settings import use_config
from trafilatura import extract_metadata
from .cache_service import cache_service

class ValueSerpService:
    def __init__(self):
        self.api_key = os.getenv("VALUESERP_API_KEY") or os.getenv("SERP_API_KEY")
        self.base_url = "https://api.valueserp.com/search"
        
    async def get_serp_data(self, query: str, location: str = "France", language: str = "fr", num_results: int = 20) -> Dict[str, Any]:
        """
        Récupère les données SERP via ValueSERP API avec cache 7 jours

        Args:
            query: Requête de recherche
            location: Localisation géographique (ex: "France")
            language: Code langue (ex: "fr")
            num_results: Nombre de résultats à récupérer (10-30)

        Returns:
            Dictionnaire contenant organic_results, paa, related_searches, inline_videos
        """
        
        # 🚀 CACHE: Vérification du cache d'abord
        cached_result = cache_service.get("serp", query, location, language, num_results)
        if cached_result is not None:
            print(f"📦 Cache HIT: SERP '{query}' (économie API + scraping)")
            return cached_result

        params = {
            "api_key": self.api_key,
            "q": query,
            "location": location,
            "google_domain": "google.fr",
            "gl": "fr",
            "hl": language,
            "num": num_results,  # MODIFIÉ : dynamique au lieu de 10
            "device": "desktop",
            "include_answer_box": "true",
            "include_people_also_ask": "true"
        }
        
        # Vérification de la clé API
        if not self.api_key:
            error_msg = "❌ ERREUR: Clé API ValueSERP manquante!"
            print(error_msg)
            print("Créez un fichier .env avec: SERP_API_KEY=votre_clé")
            print("Ou configurez la variable d'environnement VALUESERP_API_KEY")
            raise Exception("Clé API ValueSERP non configurée. Vérifiez votre fichier .env")
        
        print(f"🔍 Recherche SERP pour: {query}")
        print(f"🔑 Clé API configurée: {self.api_key[:10]}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                print(f"📡 Statut réponse: {response.status_code}")
                response.raise_for_status()
                serp_data = response.json()
                
                # Debug des données reçues
                print(f"📊 Données reçues - organic_results: {len(serp_data.get('organic_results', []))}")
                print(f"📊 Données reçues - people_also_ask: {len(serp_data.get('people_also_ask', []))}")
                
                # Debug des données (commenté pour éviter les problèmes de fichiers)
                # import json
                # try:
                #     with open('debug_serp_data.json', 'w', encoding='utf-8') as f:
                #         json.dump(serp_data, f, indent=2, ensure_ascii=False)
                #     print("📄 Données SERP exportées dans debug_serp_data.json")
                # except:
                #     pass
                
                if not serp_data.get('organic_results'):
                    error_msg = f"⚠️ Aucun résultat organique trouvé pour '{query}'"
                    print(error_msg)
                    print("Vérifiez que votre clé API ValueSERP est valide et active")
                    raise Exception(f"Aucun résultat SERP trouvé pour la requête: {query}")

                # ⭐ NOUVEAU : Utiliser le scraping parallèle
                organic_results = await self._process_serp_results_parallel(serp_data, num_results)
                
                # Extraction de tous les éléments SERP
                paa_questions = self._extract_paa(serp_data)
                related_searches = self._extract_related_searches(serp_data)
                inline_videos = self._extract_inline_videos(serp_data)
                
                final_result = {
                    'organic_results': organic_results,
                    'paa': paa_questions,
                    'related_searches': related_searches,
                    'inline_videos': inline_videos
                }
                
                # 💾 CACHE: Stocker le résultat pour 7 jours
                cache_service.set("serp", final_result, query, location, language, num_results)
                print(f"💾 Cache MISS: SERP '{query}' → stocké 7j")
                
                return final_result
                
            except httpx.HTTPError as e:
                error_msg = f"Erreur HTTP lors de l'appel à ValueSERP: {e}"
                print(error_msg)
                print("Vérifiez votre clé API ValueSERP dans le fichier .env")
                print("Ou vérifiez votre connexion internet")
                raise Exception(f"Erreur de connexion à l'API ValueSERP: {e}")
            except Exception as e:
                error_msg = f"Erreur générale lors de l'appel ValueSERP: {e}"
                print(error_msg)
                if 'serp_data' in locals():
                    print(f"Données reçues: {serp_data}")
                raise Exception(f"Erreur lors de l'analyse SERP: {e}")
    
    async def _process_serp_results(self, serp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Traite les résultats SERP pour extraire les informations nécessaires (DEPRECATED - utiliser _process_serp_results_parallel)"""
        results = []

        if "organic_results" in serp_data:
            for result in serp_data["organic_results"]:
                processed_result = {
                    "position": result.get("position", 0),
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "domain": self._extract_domain(result.get("link", "")),
                }

                # Récupération du contenu de la page
                content_data = await self._fetch_page_content(result.get("link", ""))
                processed_result.update(content_data)

                results.append(processed_result)

        return results

    async def _process_serp_results_parallel(self, serp_data: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Traite les résultats SERP en PARALLÈLE pour extraire les informations nécessaires

        Args:
            serp_data: Données brutes de ValueSERP
            max_results: Nombre maximum de résultats à traiter (10 ou 20)

        Returns:
            Liste des résultats traités avec contenu extrait
        """
        if "organic_results" not in serp_data:
            return []

        organic_results = serp_data["organic_results"][:max_results]

        # Création des tâches parallèles
        tasks = []
        for result in organic_results:
            base_data = {
                "position": result.get("position", 0),
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "domain": self._extract_domain(result.get("link", "")),
            }

            # Tâche de scraping pour cette page
            task = self._fetch_and_merge_content(result.get("link", ""), base_data)
            tasks.append(task)

        # Exécution en PARALLÈLE
        print(f"🚀 Lancement du scraping parallèle de {len(tasks)} pages...")
        import time
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        print(f"✅ Scraping parallèle terminé en {elapsed:.2f}s")

        # Filtrage des erreurs
        valid_results = []
        error_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_count += 1
                print(f"⚠️ Erreur page #{i+1}: {str(result)[:100]}")
                # Ajouter un résultat vide pour maintenir la cohérence
                valid_results.append({
                    "position": i + 1,
                    "title": organic_results[i].get("title", ""),
                    "url": organic_results[i].get("link", ""),
                    "snippet": organic_results[i].get("snippet", ""),
                    "domain": self._extract_domain(organic_results[i].get("link", "")),
                    "content": "",
                    "word_count": 0,
                    "h1": "",
                    "h2": "",
                    "h3": "",
                    "author": "",
                    "date": "",
                    "description": "",
                    "sitename": "",
                    "language": "fr",
                    "internal_links": 0,
                    "external_links": 0,
                    "images": 0,
                    "tables": 0,
                    "lists": 0,
                    "videos": 0,
                    "titles": 0,
                    "content_quality": "error",
                    "scraping_error": True
                })
            else:
                valid_results.append(result)

        print(f"📊 Résultats valides: {len(valid_results) - error_count}/{len(results)}")

        return valid_results

    async def _fetch_and_merge_content(self, url: str, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Récupère le contenu d'une page et fusionne avec les données de base
        Version optimisée avec gestion d'erreur
        """
        try:
            content_data = await self._fetch_page_content(url)
            return {**base_data, **content_data}
        except Exception as e:
            print(f"❌ Erreur scraping {url}: {str(e)[:50]}")
            # Retourner données de base sans contenu
            return {
                **base_data,
                "content": "",
                "word_count": 0,
                "h1": "",
                "h2": "",
                "h3": "",
                "author": "",
                "date": "",
                "description": "",
                "sitename": "",
                "language": "fr",
                "internal_links": 0,
                "external_links": 0,
                "images": 0,
                "tables": 0,
                "lists": 0,
                "videos": 0,
                "titles": 0,
                "content_quality": "error"
            }
    
    async def _fetch_page_content(self, url: str) -> Dict[str, Any]:
        """Récupère le contenu d'une page web pour analyse avec cache 7 jours"""
        
        # 🚀 CACHE: Vérification du cache d'abord  
        cached_content = cache_service.get("content", url)
        if cached_content is not None:
            print(f"📦 Cache HIT: {url[:50]}...")
            return cached_content

        # OPTIMISÉ : Timeout réduit à 10s (5s connexion + 10s total)
        timeout = httpx.Timeout(10.0, connect=5.0)

        # Headers améliorés pour éviter blocage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            print(f"🔍 Récupération: {url[:60]}...")
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    html_content = response.text
                    
                    # NOUVELLE APPROCHE: Extraction avec trafilatura + métadonnées
                    main_content = self._extract_content_with_trafilatura(html_content, url)
                    metadata = self._extract_metadata_with_trafilatura(html_content)
                    
                    # BeautifulSoup uniquement pour les statistiques HTML
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Comptage des mots basé sur le contenu extrait par trafilatura
                    word_count = len(main_content.split()) if main_content else 0
                    
                    # Validation améliorée de la qualité
                    content_quality = self._validate_content_quality_v2(main_content, word_count, metadata)
                    
                    result = {
                        # Métadonnées extraites par trafilatura
                        "h1": metadata.get('title') or self._extract_h1(soup),
                        "h2": self._extract_h2(soup),  # Garde l'ancienne méthode pour H2/H3
                        "h3": self._extract_h3(soup),
                        
                        # Contenu principal (trafilatura)
                        "content": main_content,
                        "word_count": word_count,
                        
                        # Métadonnées enrichies
                        "author": metadata.get('author', ''),
                        "date": metadata.get('date', ''),
                        "description": metadata.get('description', ''),
                        "sitename": metadata.get('sitename', ''),
                        "language": metadata.get('language', 'fr'),
                        
                        # Statistiques HTML (BeautifulSoup)
                        "internal_links": len(soup.find_all('a', href=lambda x: x and not x.startswith('http'))),
                        "external_links": len(soup.find_all('a', href=lambda x: x and x.startswith('http'))),
                        "images": len(soup.find_all('img')),
                        "tables": len(soup.find_all('table')),
                        "lists": len(soup.find_all(['ul', 'ol'])),
                        "videos": len(soup.find_all(['video', 'iframe'])),
                        "titles": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                        
                        # Qualité calculée
                        "content_quality": content_quality
                    }
                    
                    print(f"✅ OK: {word_count} mots, qualité: {content_quality}")
                    
                    # 💾 CACHE: Stocker le contenu si valide
                    if word_count > 0:
                        cache_service.set("content", result, url)
                        print(f"💾 Cache MISS: {url[:50]}... → stocké 7j")
                    
                    return result
                else:
                    print(f"⚠️ HTTP {response.status_code}")
                    raise Exception(f"HTTP {response.status_code}")

        except httpx.TimeoutException:
            print(f"⏱️ Timeout pour {url[:50]}")
            raise Exception("Timeout")
        except Exception as e:
            print(f"❌ Erreur: {str(e)[:50]}")
            raise
            
        return {
            "h1": "",
            "h2": "",
            "h3": "",
            "content": "",
            "word_count": 0,
            "author": "",
            "date": "",
            "description": "",
            "sitename": "",
            "language": "fr",
            "internal_links": 0,
            "external_links": 0,
            "images": 0,
            "tables": 0,
            "lists": 0,
            "videos": 0,
            "titles": 0,
            "content_quality": "failed"
        }
    
    def _validate_content_quality(self, content: str, word_count: int) -> str:
        """Valide la qualité du contenu extrait - Version assouplie"""
        if not content or not content.strip():
            return "empty"
        
        # Seuils beaucoup plus permissifs
        if word_count < 20:  # Était 50, maintenant 20
            return "too_short"
        
        if word_count < 100:  # Était 200, maintenant 100
            return "short"
        
        # Vérifier si le contenu semble être principalement du menu/navigation
        navigation_indicators = [
            'accueil', 'contact', 'mentions légales', 'politique de confidentialité',
            'conditions générales', 'plan du site', 'newsletter', 'suivez-nous',
            'réseaux sociaux', 'twitter', 'facebook', 'instagram', 'linkedin'
        ]
        
        content_lower = content.lower()
        nav_matches = sum(1 for indicator in navigation_indicators if indicator in content_lower)
        
        # Seuil plus permissif pour la navigation
        if nav_matches > 8 and word_count < 200:  # Était 5 et 500, maintenant 8 et 200
            return "mostly_navigation"
        
        # Seuils plus permissifs pour les qualités
        if word_count > 800:  # Était 1000
            return "excellent"
        elif word_count > 300:  # Était 500
            return "good"
        elif word_count > 50:  # Nouveau seuil
            return "acceptable"
        else:
            return "short"

    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""
    
    def _extract_h1(self, soup: BeautifulSoup) -> str:
        """Extrait le H1 principal"""
        h1 = soup.find('h1')
        return h1.get_text().strip() if h1 else ""
    
    def _extract_h2(self, soup: BeautifulSoup) -> str:
        """Extrait le premier H2"""
        h2 = soup.find('h2')
        return h2.get_text().strip() if h2 else ""
    
    def _extract_h3(self, soup: BeautifulSoup) -> str:
        """Extrait le premier H3"""
        h3 = soup.find('h3')
        return h3.get_text().strip() if h3 else ""
    
    def _extract_content_with_trafilatura(self, html_content: str, url: str = "") -> str:
        """Extrait le contenu principal avec trafilatura hybride intelligent"""
        try:
            # STRATÉGIE 1: Trafilatura mode précision (pour sites bien structurés)
            content_precise = self._try_trafilatura_precise(html_content, url)
            
            # STRATÉGIE 2: Si contenu insuffisant, essayer mode agressif
            if not content_precise or len(content_precise.split()) < 100:
                print("📄 Contenu trafilatura précis insuffisant, essai mode agressif")
                content_aggressive = self._try_trafilatura_aggressive(html_content, url)
                
                # Prendre le plus long entre précis et agressif
                if content_aggressive and len(content_aggressive.split()) > len(content_precise.split() if content_precise else []):
                    content_precise = content_aggressive
            
            # STRATÉGIE 3: Si toujours insuffisant, utiliser BeautifulSoup hybride
            if not content_precise or len(content_precise.split()) < 50:
                print("📄 Trafilatura insuffisant, utilisation BeautifulSoup hybride")
                return self._extract_content_beautifulsoup_smart(html_content)
            
            word_count = len(content_precise.split())
            print(f"📄 Trafilatura hybride: contenu extrait ({word_count} mots)")
            return content_precise.strip()
                
        except Exception as e:
            print(f"📄 Erreur trafilatura hybride: {e}, fallback BeautifulSoup")
            return self._extract_content_beautifulsoup_smart(html_content)
    
    def _try_trafilatura_precise(self, html_content: str, url: str) -> str:
        """Trafilatura mode précision"""
        try:
            config = use_config()
            config.set('DEFAULT', 'EXTRACTION_TIMEOUT', '30')
            
            content = trafilatura.extract(
                html_content,
                url=url,
                config=config,
                include_comments=False,
                include_tables=True,
                include_links=False,
                include_images=False,
                include_formatting=False,
                output_format='txt',
                target_language='fr',
                deduplicate=True,
                favor_precision=True
            )
            
            return content or ""
        except:
            return ""
    
    def _try_trafilatura_aggressive(self, html_content: str, url: str) -> str:
        """Trafilatura mode agressif (plus de contenu)"""
        try:
            config = use_config()
            config.set('DEFAULT', 'MIN_EXTRACTED_SIZE', '25')  # Seuil plus bas
            config.set('DEFAULT', 'MIN_OUTPUT_SIZE', '25')
            
            content = trafilatura.extract(
                html_content,
                url=url,
                config=config,
                include_comments=False,
                include_tables=True,
                include_links=True,        # INCLURE LIENS
                include_images=False,
                include_formatting=True,   # INCLURE FORMATAGE
                output_format='txt',
                target_language=None,      # PAS DE FILTRE LANGUE
                deduplicate=False,         # PAS DE DÉDUPLICATION
                favor_precision=False,     # PRIVILÉGIER RAPPEL
                favor_recall=True
            )
            
            return content or ""
        except:
            return ""
    
    def _extract_content_beautifulsoup_smart(self, html_content: str) -> str:
        """BeautifulSoup intelligent avec stratégie progressive"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # STRATÉGIE 1: Essai avec sélecteurs standards (sans suppression)
            standard_selectors = ['main', 'article', '[role="main"]', '.main-content', '.content', '.entry-content']
            
            for selector in standard_selectors:
                elements = soup.select(selector)
                if elements:
                    best_element = max(elements, key=lambda e: len(e.get_text()))
                    content = best_element.get_text(separator=' ', strip=True)
                    word_count = len(content.split())
                    
                    if word_count >= 100:  # Contenu substantiel
                        print(f"📄 BeautifulSoup smart: sélecteur standard '{selector}' ({word_count} mots)")
                        return self._smart_clean_text(content)
            
            # STRATÉGIE 2: Body complet avec nettoyage léger
            print("📄 BeautifulSoup smart: utilisation du body avec nettoyage léger")
            
            # Copie pour nettoyage
            soup_clean = BeautifulSoup(html_content, 'html.parser')
            
            # Suppression minimale et intelligente
            elements_to_remove = [
                # Scripts et styles (obligatoire)
                'script', 'style', 'noscript',
                # Navigation très spécifique seulement
                'nav.main-navigation', 'nav#main-navigation',
                '.site-navigation', '#site-navigation',
                # Footer spécifique
                'footer.site-footer', '#site-footer',
                # Éléments publicitaires évidents
                '.advertisement', '.ads', '.ad-banner'
            ]
            
            for selector in elements_to_remove:
                for element in soup_clean.select(selector):
                    element.decompose()
            
            # Extraction du body nettoyé
            body = soup_clean.find('body')
            if body:
                content = body.get_text(separator=' ', strip=True)
                content = self._smart_clean_text(content)
                word_count = len(content.split())
                
                if word_count >= 50:
                    print(f"📄 BeautifulSoup smart: body nettoyé ({word_count} mots)")
                    return content
            
            # STRATÉGIE 3: Body brut en dernier recours
            print("📄 BeautifulSoup smart: body brut en dernier recours")
            raw_body = soup.find('body')
            if raw_body:
                content = raw_body.get_text(separator=' ', strip=True)
                content = self._smart_clean_text(content)
                word_count = len(content.split())
                
                print(f"📄 BeautifulSoup smart: body brut ({word_count} mots)")
                return content
            
            return ""
            
        except Exception as e:
            print(f"📄 Erreur BeautifulSoup smart: {e}")
            return ""
    
    def _smart_clean_text(self, text: str) -> str:
        """Nettoyage intelligent du texte extrait"""
        import re
        
        # Normalise les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprime les répétitions excessives de mots courts
        words = text.split()
        clean_words = []
        prev_word = ""
        repeat_count = 0
        
        for word in words:
            if word.lower() == prev_word.lower() and len(word) <= 4:
                repeat_count += 1
                if repeat_count < 2:  # Autorise 1 répétition
                    clean_words.append(word)
            else:
                clean_words.append(word)
                repeat_count = 0
            prev_word = word
        
        return ' '.join(clean_words).strip()
    
    def _extract_content_fallback(self, html_content: str) -> str:
        """OBSOLÈTE: Remplacé par _extract_content_beautifulsoup_smart"""
        # Redirection vers la nouvelle méthode smart
        return self._extract_content_beautifulsoup_smart(html_content)
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Wrapper pour compatibilité - utilise trafilatura"""
        html_content = str(soup)
        return self._extract_content_with_trafilatura(html_content)
    
    def _count_words(self, soup: BeautifulSoup) -> int:
        """Compte le nombre de mots dans le contenu principal"""
        text = self._extract_content(soup)
        if not text.strip():
            return 0
        
        # Nettoyage du texte pour un comptage plus précis
        clean_text = ' '.join(text.split())  # Supprime les espaces multiples
        word_count = len(clean_text.split())
        
        print(f"📊 Nombre de mots dans le contenu principal: {word_count}")
        return word_count
    
    def _extract_metadata_with_trafilatura(self, html_content: str) -> Dict[str, str]:
        """Extrait les métadonnées avec trafilatura"""
        try:
            metadata = extract_metadata(html_content)
            
            if metadata:
                return {
                    'title': metadata.title or '',
                    'author': metadata.author or '',
                    'date': str(metadata.date) if metadata.date else '',
                    'description': metadata.description or '',
                    'sitename': metadata.sitename or '',
                    'language': metadata.language or 'fr',
                    'url': metadata.url or '',
                    'categories': ', '.join(metadata.categories) if metadata.categories else '',
                    'tags': ', '.join(metadata.tags) if metadata.tags else ''
                }
            else:
                return {}
                
        except Exception as e:
            print(f"📄 Erreur extraction métadonnées: {e}")
            return {}
    
    def _validate_content_quality_v2(self, content: str, word_count: int, metadata: Dict[str, str]) -> str:
        """Validation améliorée de la qualité du contenu avec métadonnées"""
        if not content or not content.strip():
            return "empty"
        
        # Seuils plus réalistes basés sur les standards web
        if word_count < 30:
            return "too_short"
        elif word_count < 100:
            return "short"
        elif word_count < 300:
            # Vérifie si c'est un contenu structuré (avec métadonnées)
            if metadata.get('author') or metadata.get('date') or len(metadata.get('title', '')) > 10:
                return "acceptable"  # Contenu court mais structuré
            else:
                return "short"
        elif word_count < 800:
            return "good"
        elif word_count < 2000:
            return "excellent"
        else:
            # Très long - vérifie la structure
            if metadata.get('author') and metadata.get('date'):
                return "comprehensive"  # Article long et bien structuré
            else:
                return "excellent"
        
        # Indicateurs de qualité supplémentaires
        quality_indicators = 0
        
        # Présence d'auteur
        if metadata.get('author'):
            quality_indicators += 1
        
        # Date de publication
        if metadata.get('date'):
            quality_indicators += 1
        
        # Description méta
        if len(metadata.get('description', '')) > 50:
            quality_indicators += 1
        
        # Titre significatif
        if len(metadata.get('title', '')) > 20:
            quality_indicators += 1
        
        # Site identifié
        if metadata.get('sitename'):
            quality_indicators += 1
        
        # Ajustement basé sur les indicateurs de qualité
        if quality_indicators >= 3 and word_count >= 200:
            return "professional"  # Contenu professionnel bien structuré
        
        return "good" if word_count >= 300 else "acceptable"
    
    def _count_words_from_content(self, content: str) -> int:
        """Compte les mots directement depuis le contenu extrait"""
        if not content or not content.strip():
            return 0
        
        # Nettoyage et comptage plus précis
        clean_content = ' '.join(content.split())  # Normalise les espaces
        word_count = len(clean_content.split())
        
        print(f"📊 Nombre de mots dans le contenu extrait: {word_count}")
        return word_count
    
    def _extract_paa(self, serp_data: Dict[str, Any]) -> List[str]:
        """Extrait les questions People Also Ask (related_questions dans ValueSERP)"""
        paa_questions = []
        
        print(f"🔍 Clés dans serp_data: {list(serp_data.keys())}")
        
        # ValueSERP utilise "related_questions" pour les PAA
        if "related_questions" in serp_data and serp_data["related_questions"]:
            print(f"✅ Trouvé related_questions avec {len(serp_data['related_questions'])} éléments")
            
            for paa_item in serp_data["related_questions"]:
                if isinstance(paa_item, dict):
                    if "question" in paa_item:
                        paa_questions.append(paa_item["question"])
                        print(f"📋 Question extraite: {paa_item['question']}")
                    elif "title" in paa_item:
                        paa_questions.append(paa_item["title"])
        else:
            print("❌ Aucune related_questions trouvée")
        
        print(f"📋 Total PAA extraites: {len(paa_questions)}")
        return paa_questions
    
    def _extract_related_searches(self, serp_data: Dict[str, Any]) -> List[str]:
        """Extrait les recherches associées"""
        related_searches = []
        
        if "related_searches" in serp_data and serp_data["related_searches"]:
            print(f"✅ Trouvé related_searches avec {len(serp_data['related_searches'])} éléments")
            
            for search_item in serp_data["related_searches"]:
                if isinstance(search_item, dict):
                    if "query" in search_item:
                        related_searches.append(search_item["query"])
                    elif "title" in search_item:
                        related_searches.append(search_item["title"])
                elif isinstance(search_item, str):
                    related_searches.append(search_item)
        
        return related_searches
    
    def _clean_wikipedia_text(self, text: str) -> str:
        """Nettoie le texte spécifique à Wikipedia"""
        import re
        
        # Patterns spécifiques à Wikipedia à supprimer
        wikipedia_patterns = [
            r'\[modifier\s*\|\s*modifier\s+le\s+code\]',  # [modifier | modifier le code]
            r'\[modifier\]',                               # [modifier]
            r'\[modifier\s+le\s+code\]',                  # [modifier le code]
            r'\[réf\.\s*souhaitée\]',                     # [réf. souhaitée]
            r'\[réf\.\s*nécessaire\]',                    # [réf. nécessaire]
            r'\[citation\s*nécessaire\]',                 # [citation nécessaire]
            r'\[source\s*insuffisante\]',                 # [source insuffisante]
            r'\[Quand\s*\?\]',                            # [Quand ?]
            r'\[Où\s*\?\]',                               # [Où ?]
            r'\[Qui\s*\?\]',                              # [Qui ?]
            r'\[Comment\s*\?\]',                          # [Comment ?]
            r'\[Pourquoi\s*\?\]',                         # [Pourquoi ?]
            r'\[style\s*à\s*revoir\]',                    # [style à revoir]
            r'\[pas\s*clair\]',                           # [pas clair]
            r'\[précision\s*nécessaire\]',                # [précision nécessaire]
            r'\[\d+\]',                                   # [1], [2], etc. (références)
            r'Article\s*détaillé\s*:',                    # Article détaillé :
            r'Voir\s*aussi\s*:',                          # Voir aussi :
            r'Catégories\s*:',                            # Catégories :
            r'Portail\s*de\s*',                           # Portail de
            r'Ce\s*document\s*provient\s*de',             # Ce document provient de
            r'Dernière\s*modification\s*de\s*cette\s*page', # Dernière modification
            r'Récupérée\s*de\s*«\s*https?://[^»]*»',      # Récupérée de « URL »
            r'Espaces\s*de\s*noms',                       # Espaces de noms
            r'Affichages',                                # Affichages
            r'Outils',                                    # Outils
            r'Imprimer\s*/\s*exporter',                   # Imprimer / exporter
            r'Dans\s*d\'autres\s*projets',               # Dans d'autres projets
            r'Dans\s*d\'autres\s*langues',               # Dans d'autres langues
            r'Wikimedia\s*Commons',                       # Wikimedia Commons
            r'Wiktionnaire',                              # Wiktionnaire
            r'Wikiquote',                                 # Wikiquote
            r'Wikinews',                                  # Wikinews
            r'Wikiversité',                               # Wikiversité
            r'Wikibooks',                                 # Wikibooks
            r'Wikisource',                                # Wikisource
            r'Wikivoyage',                                # Wikivoyage
        ]
        
        # Applique tous les patterns
        for pattern in wikipedia_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Nettoie les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_inline_videos(self, serp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les vidéos intégrées"""
        videos = []
        
        if "inline_videos" in serp_data and serp_data["inline_videos"]:
            print(f"✅ Trouvé inline_videos avec {len(serp_data['inline_videos'])} éléments")
            
            for video_item in serp_data["inline_videos"]:
                if isinstance(video_item, dict):
                    video_data = {
                        "title": video_item.get("title", ""),
                        "link": video_item.get("link", ""),
                        "thumbnail": video_item.get("thumbnail", ""),
                        "duration": video_item.get("duration", ""),
                        "source": video_item.get("source", "")
                    }
                    videos.append(video_data)
        
        return videos
    
    def _get_demo_data(self, query: str) -> Dict[str, Any]:
        """Retourne des données de démonstration adaptées à la requête"""
        
        # Données adaptées selon la requête
        if "seo" in query.lower() and "lille" in query.lower():
            return {
                'organic_results': [
                    {
                        "position": 1,
                        "title": "Agence SEO Lille - Référencement naturel et digital",
                        "url": "https://www.agence-seo-lille.fr/",
                        "domain": "agence-seo-lille.fr",
                        "h1": "Agence SEO spécialisée à Lille",
                        "h2": "Services de référencement naturel",
                        "h3": "Audit SEO gratuit",
                        "word_count": 1200,
                        "internal_links": 15,
                        "external_links": 3,
                        "images": 8,
                        "tables": 1,
                        "lists": 5,
                        "videos": 0,
                        "titles": 6,
                        "content": "Agence SEO Lille spécialisée référencement naturel digital marketing. Notre agence SEO à Lille propose des services de référencement naturel complets pour améliorer votre visibilité sur Google. Experts en SEO depuis 10 ans, nous accompagnons les entreprises lilloises dans leur stratégie de référencement naturel. Audit SEO gratuit, optimisation technique, rédaction de contenu SEO, netlinking... Notre équipe SEO maîtrise tous les aspects du référencement naturel pour positionner votre site en première page de Google. Contactez notre agence SEO à Lille pour un devis personnalisé."
                    },
                    {
                        "position": 2,
                        "title": "Référencement SEO Lille - Consultant expert",
                        "url": "https://consultant-seo-lille.com/",
                        "domain": "consultant-seo-lille.com",
                        "h1": "Consultant SEO à Lille",
                        "h2": "Expertise en référencement naturel",
                        "h3": "Stratégie SEO personnalisée",
                        "word_count": 980,
                        "internal_links": 12,
                        "external_links": 5,
                        "images": 6,
                        "tables": 0,
                        "lists": 3,
                        "videos": 1,
                        "titles": 4,
                        "content": "Consultant SEO Lille expert référencement naturel Google. Spécialiste SEO indépendant basé à Lille, j'aide les entreprises à améliorer leur référencement naturel sur Google. Mes prestations SEO incluent l'audit technique, l'optimisation on-page, la stratégie de contenu SEO et le netlinking. Fort de 8 ans d'expérience en SEO, je vous accompagne dans votre stratégie de référencement naturel pour obtenir plus de trafic qualifié. Consultant SEO certifié Google, je propose des services personnalisés adaptés à vos objectifs business. Formation SEO, accompagnement mensuel, audit SEO complet... Contactez-moi pour booster votre référencement naturel à Lille."
                    }
                ],
                'paa': [
                    "Quelle est la meilleure agence SEO à Lille ?",
                    "Combien coûte le référencement naturel à Lille ?",
                    "Comment choisir son consultant SEO à Lille ?",
                    "Quel est le prix d'un audit SEO à Lille ?"
                ],
                'related_searches': [
                    "agence seo lille prix",
                    "consultant seo lille",
                    "referencement naturel lille",
                    "agence digitale lille",
                    "audit seo lille gratuit",
                    "formation seo lille",
                    "freelance seo lille",
                    "agence web lille"
                ],
                'inline_videos': [
                    {
                        "title": "Comment choisir son agence SEO à Lille",
                        "link": "https://youtube.com/watch?v=example1",
                        "thumbnail": "https://img.youtube.com/vi/example1/hqdefault.jpg",
                        "duration": "5:32",
                        "source": "YouTube"
                    },
                    {
                        "title": "Audit SEO gratuit Lille - Tutoriel",
                        "link": "https://youtube.com/watch?v=example2",
                        "thumbnail": "https://img.youtube.com/vi/example2/hqdefault.jpg",
                        "duration": "8:15",
                        "source": "YouTube"
                    }
                ]
            }
        
        # Données par défaut (créatine)
        return {
            'organic_results': [
            {
                "position": 2,
                "title": "Créatine et prise de masse : à quoi s'attendre réellement ?",
                "url": "https://nutriandco.com/fr/pages/creatine-prise-de-masse",
                "domain": "nutriandco.com",
                "h1": "Quels sont les bienfaits de la créatine sur la prise de masse ?",
                "h2": "Comment prendre de la créatine pour faire une prise de masse ?",
                "h3": "Quand prendre de la créatine pour une prise de masse ?",
                "word_count": 1675,
                "internal_links": 12,
                "external_links": 0,
                "images": 54,
                "tables": 0,
                "lists": 2,
                "videos": 0,
                "titles": 8,
                "content": "Contenu de démonstration pour l'analyse sémantique..."
            },
            {
                "position": 3,
                "title": "créatine whey ou bcaa : quel complément choisir et pourquoi ?",
                "url": "https://www.inshape-nutrition.com/blogs/article/creatine-whey-ou-bcaa-quel-complement-choisir-et-pourquoi",
                "domain": "www.inshape-nutrition.com",
                "h1": " ",
                "h2": "Peut-on mélanger whey et bcaa dans un seul shaker ?",
                "h3": "",
                "word_count": 906,
                "internal_links": 11,
                "external_links": 6,
                "images": 6,
                "tables": 0,
                "lists": 6,
                "videos": 0,
                "titles": 6,
                "content": "Contenu de démonstration pour l'analyse sémantique..."
            }
            ],
            'paa': [
                "Quel est le mieux entre la créatine et la whey ?",
                "Est-ce qu'on peut mélanger la créatine et la whey ?",
                "Quelle est la différence entre la créatine et la protéine ?",
                "Comment prendre de la créatine et de la whey ?"
            ],
            'related_searches': [
                "creatine monohydrate",
                "creatine whey protein",
                "creatine prise de masse",
                "creatine effets secondaires",
                "meilleure creatine",
                "creatine avant ou apres entrainement",
                "creatine dosage",
                "creatine bcaa"
            ],
            'inline_videos': [
                {
                    "title": "Créatine : Comment la prendre correctement",
                    "link": "https://youtube.com/watch?v=creatine1",
                    "thumbnail": "https://img.youtube.com/vi/creatine1/hqdefault.jpg",
                    "duration": "12:45",
                    "source": "YouTube"
                },
                {
                    "title": "Créatine vs Whey : Quelle différence ?",
                    "link": "https://youtube.com/watch?v=creatine2",
                    "thumbnail": "https://img.youtube.com/vi/creatine2/hqdefault.jpg",
                    "duration": "9:20",
                    "source": "YouTube"
                }
            ]
        } 