import httpx
import os
from typing import Dict, List, Any
import asyncio
from bs4 import BeautifulSoup

class ValueSerpService:
    def __init__(self):
        self.api_key = os.getenv("VALUESERP_API_KEY") or os.getenv("SERP_API_KEY")
        self.base_url = "https://api.valueserp.com/search"
        
    async def get_serp_data(self, query: str, location: str = "France", language: str = "fr") -> Dict[str, Any]:
        """Récupère les données SERP via ValueSERP API"""
        
        params = {
            "api_key": self.api_key,
            "q": query,
            "location": location,
            "google_domain": "google.fr",
            "gl": "fr",
            "hl": language,
            "num": 10,
            "device": "desktop",
            "include_answer_box": "true",
            "include_people_also_ask": "true"
        }
        
        # Vérification de la clé API
        if not self.api_key:
            print("❌ ERREUR: Clé API ValueSERP manquante!")
            print("Créez un fichier .env avec: SERP_API_KEY=votre_clé")
            return self._get_demo_data(query)
        
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
                    print("⚠️ Aucun résultat organique trouvé, utilisation des données de démonstration")
                    return self._get_demo_data(query)
                
                # Traitement des résultats
                organic_results = await self._process_serp_results(serp_data)
                
                # Extraction de tous les éléments SERP
                paa_questions = self._extract_paa(serp_data)
                related_searches = self._extract_related_searches(serp_data)
                inline_videos = self._extract_inline_videos(serp_data)
                
                return {
                    'organic_results': organic_results,
                    'paa': paa_questions,
                    'related_searches': related_searches,
                    'inline_videos': inline_videos
                }
                
            except httpx.HTTPError as e:
                print(f"Erreur HTTP lors de l'appel à ValueSERP: {e}")
                print(f"Vérifiez votre clé API ValueSERP dans le fichier .env")
                # Retourner des données de démonstration en cas d'erreur
                return self._get_demo_data(query)
            except Exception as e:
                print(f"Erreur générale: {e}")
                print(f"Données reçues: {serp_data if 'serp_data' in locals() else 'Aucune donnée'}")
                return self._get_demo_data(query)
    
    async def _process_serp_results(self, serp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Traite les résultats SERP pour extraire les informations nécessaires"""
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
    
    async def _fetch_page_content(self, url: str) -> Dict[str, Any]:
        """Récupère le contenu d'une page web pour analyse"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    return {
                        "h1": self._extract_h1(soup),
                        "h2": self._extract_h2(soup),
                        "h3": self._extract_h3(soup),
                        "content": self._extract_content(soup),
                        "word_count": self._count_words(soup),
                        "internal_links": len(soup.find_all('a', href=lambda x: x and not x.startswith('http'))),
                        "external_links": len(soup.find_all('a', href=lambda x: x and x.startswith('http'))),
                        "images": len(soup.find_all('img')),
                        "tables": len(soup.find_all('table')),
                        "lists": len(soup.find_all(['ul', 'ol'])),
                        "videos": len(soup.find_all(['video', 'iframe'])),
                        "titles": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
                    }
        except Exception as e:
            print(f"Erreur lors de la récupération du contenu de {url}: {e}")
            
        return {
            "h1": "",
            "h2": "",
            "h3": "",
            "content": "",
            "word_count": 0,
            "internal_links": 0,
            "external_links": 0,
            "images": 0,
            "tables": 0,
            "lists": 0,
            "videos": 0,
            "titles": 0
        }
    
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
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extrait le contenu textuel principal"""
        # Supprime les scripts et styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text()
    
    def _count_words(self, soup: BeautifulSoup) -> int:
        """Compte le nombre de mots dans le contenu"""
        text = self._extract_content(soup)
        return len(text.split())
    
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