#!/usr/bin/env python3
"""
Version améliorée du ValueSerpService avec User-Agent rotatif,
gestion des redirections et fallback URLs
"""

import httpx
import os
import random
import time
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.settings import use_config
from trafilatura import extract_metadata

class EnhancedValueSerpService:
    def __init__(self):
        self.api_key = os.getenv("VALUESERP_API_KEY") or os.getenv("SERP_API_KEY")
        self.base_url = "https://api.valueserp.com/search"
        
        # 🔄 1. USER-AGENTS ROTATIFS RÉALISTES
        self.user_agents = [
            # Chrome Windows (les plus courants)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            
            # Firefox Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            
            # Edge Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # Chrome macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Safari macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            
            # Chrome Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Mobile Chrome Android (pour sites mobiles)
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            
            # Mobile Safari iPhone
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        ]
        
        # Headers additionnels réalistes
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }
        
        # Cache des User-Agents par domaine
        self._domain_user_agents = {}
        
        # 📊 3. FALLBACK URLs pour domaines connus
        self.domain_fallbacks = {
            'service-public.fr': [
                'https://www.service-public.fr/',
                'https://www.service-public.fr/particuliers',
                'https://www.service-public.fr/professionnels'
            ],
            'economie.gouv.fr': [
                'https://www.economie.gouv.fr/',
                'https://www.economie.gouv.fr/entreprises',
                'https://www.bercy.gouv.fr/'
            ],
            'bpifrance.fr': [
                'https://www.bpifrance.fr/',
                'https://www.bpifrance.fr/nos-solutions',
                'https://www.bpifrance.fr/creation-entreprise'
            ],
            'pole-emploi.fr': [
                'https://www.pole-emploi.fr/',
                'https://candidat.pole-emploi.fr/',
                'https://www.francetravail.fr/'  # Nouveau nom
            ],
            'wikipedia.org': [
                'https://fr.wikipedia.org/wiki/Accueil',
                'https://fr.wikipedia.org/'
            ]
        }
    
    def _get_user_agent_for_domain(self, domain: str) -> str:
        """Récupère un User-Agent consistant pour un domaine"""
        
        # Utilise le même User-Agent pour le même domaine (évite détection)
        if domain not in self._domain_user_agents:
            # Choix intelligent selon le type de site
            if any(gov_domain in domain for gov_domain in ['gouv.fr', 'service-public.fr']):
                # Sites gouvernementaux : privilégier Chrome Windows (plus courant)
                gov_agents = [ua for ua in self.user_agents if 'Windows' in ua and 'Chrome' in ua]
                self._domain_user_agents[domain] = random.choice(gov_agents)
            elif 'wikipedia.org' in domain:
                # Wikipedia : tous User-Agents acceptés
                self._domain_user_agents[domain] = random.choice(self.user_agents)
            elif any(corp in domain for corp in ['.com', '.fr', '.eu']):
                # Sites commerciaux : privilégier les plus courants
                common_agents = self.user_agents[:8]  # Top 8
                self._domain_user_agents[domain] = random.choice(common_agents)
            else:
                # Par défaut
                self._domain_user_agents[domain] = random.choice(self.user_agents)
        
        return self._domain_user_agents[domain]
    
    def _get_headers_for_domain(self, domain: str, referer: Optional[str] = None) -> Dict[str, str]:
        """Génère headers réalistes pour un domaine"""
        
        headers = self.base_headers.copy()
        headers['User-Agent'] = self._get_user_agent_for_domain(domain)
        
        # Referer réaliste
        if referer:
            headers['Referer'] = referer
        elif 'google' not in domain:  # Simule arrivée depuis Google
            headers['Referer'] = 'https://www.google.fr/'
        
        # Headers spécifiques aux sites gouvernementaux
        if any(gov in domain for gov in ['gouv.fr', 'service-public.fr']):
            headers['Accept-Language'] = 'fr-FR,fr;q=0.9'  # Français uniquement
            headers['Cache-Control'] = 'max-age=0'
        
        return headers
    
    async def _fetch_page_content_enhanced(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """Version améliorée avec User-Agent rotatif et gestion redirections"""
        
        domain = self._extract_domain(url)
        print(f"🔍 Récupération améliorée: {url}")
        print(f"   🌐 Domaine: {domain}")
        
        for attempt in range(max_retries):
            try:
                # Headers adaptatifs par domaine
                headers = self._get_headers_for_domain(domain)
                user_agent = headers['User-Agent']
                
                print(f"   🤖 User-Agent #{attempt+1}: {user_agent[:50]}...")
                
                # 🔄 2. GESTION REDIRECTIONS AUTOMATIQUES
                async with httpx.AsyncClient(
                    timeout=20.0,
                    follow_redirects=True,  # ACTIVE redirections auto
                    max_redirects=5,        # Maximum 5 redirections
                    headers=headers
                ) as client:
                    
                    response = await client.get(url)
                    
                    # Log des redirections
                    if hasattr(response, 'history') and response.history:
                        print(f"   🔄 Redirections: {len(response.history)} étapes")
                        for i, redirect in enumerate(response.history, 1):
                            print(f"      {i}. {redirect.status_code} → {redirect.url}")
                        print(f"   ✅ URL finale: {response.url}")
                    
                    # Succès
                    if response.status_code == 200:
                        html_content = response.text
                        
                        # Extraction avec méthodes hybrides
                        main_content = self._extract_content_with_trafilatura(html_content, str(response.url))
                        metadata = self._extract_metadata_with_trafilatura(html_content)
                        
                        # Stats BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        word_count = len(main_content.split()) if main_content else 0
                        content_quality = self._validate_content_quality_v2(main_content, word_count, metadata)
                        
                        result = {
                            "h1": metadata.get('title') or self._extract_h1(soup),
                            "h2": self._extract_h2(soup),
                            "h3": self._extract_h3(soup),
                            "content": main_content,
                            "word_count": word_count,
                            "author": metadata.get('author', ''),
                            "date": metadata.get('date', ''),
                            "description": metadata.get('description', ''),
                            "sitename": metadata.get('sitename', ''),
                            "language": metadata.get('language', 'fr'),
                            "internal_links": len(soup.find_all('a', href=lambda x: x and not x.startswith('http'))),
                            "external_links": len(soup.find_all('a', href=lambda x: x and x.startswith('http'))),
                            "images": len(soup.find_all('img')),
                            "tables": len(soup.find_all('table')),
                            "lists": len(soup.find_all(['ul', 'ol'])),
                            "videos": len(soup.find_all(['video', 'iframe'])),
                            "titles": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                            "content_quality": content_quality,
                            "final_url": str(response.url),  # URL après redirections
                            "redirects_count": len(response.history) if hasattr(response, 'history') else 0,
                            "user_agent_used": user_agent
                        }
                        
                        print(f"   ✅ Succès: {word_count} mots, qualité: {content_quality}")
                        return result
                    
                    # Erreurs récupérables : retry avec autre User-Agent
                    elif response.status_code in [403, 429, 503]:
                        print(f"   ⚠️ Erreur {response.status_code} (récupérable), retry #{attempt+1}")
                        if attempt < max_retries - 1:
                            # Pause progressive
                            await asyncio.sleep(2 ** attempt)
                            continue
                    
                    # Autres erreurs HTTP
                    else:
                        print(f"   ❌ Erreur HTTP {response.status_code}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        break
                        
            except httpx.TimeoutException:
                print(f"   ⏰ Timeout (tentative {attempt+1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                    
            except Exception as e:
                print(f"   ❌ Erreur: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                break
        
        # 📊 3. FALLBACK URLs si échec total
        print(f"   🔄 Échec sur {url}, tentative fallback...")
        fallback_result = await self._try_fallback_urls(domain)
        
        if fallback_result:
            return fallback_result
        
        # Échec final
        return self._get_empty_result()
    
    async def _try_fallback_urls(self, domain: str) -> Optional[Dict[str, Any]]:
        """Essaie les URLs de fallback pour un domaine"""
        
        if domain not in self.domain_fallbacks:
            print(f"   ❌ Aucun fallback configuré pour {domain}")
            return None
        
        fallback_urls = self.domain_fallbacks[domain]
        print(f"   🔄 Tentative {len(fallback_urls)} URLs de fallback pour {domain}")
        
        for i, fallback_url in enumerate(fallback_urls, 1):
            print(f"      [{i}/{len(fallback_urls)}] Fallback: {fallback_url}")
            
            try:
                headers = self._get_headers_for_domain(domain)
                
                async with httpx.AsyncClient(
                    timeout=15.0, 
                    follow_redirects=True,
                    max_redirects=3,
                    headers=headers
                ) as client:
                    
                    response = await client.get(fallback_url)
                    
                    if response.status_code == 200:
                        html_content = response.text
                        main_content = self._extract_content_with_trafilatura(html_content, fallback_url)
                        
                        if main_content and len(main_content.split()) > 50:
                            print(f"      ✅ Fallback réussi: {len(main_content.split())} mots")
                            
                            # Construction résultat minimal
                            metadata = self._extract_metadata_with_trafilatura(html_content)
                            soup = BeautifulSoup(html_content, 'html.parser')
                            word_count = len(main_content.split())
                            
                            return {
                                "h1": metadata.get('title') or self._extract_h1(soup),
                                "content": main_content,
                                "word_count": word_count,
                                "content_quality": "fallback_success",
                                "author": metadata.get('author', ''),
                                "date": metadata.get('date', ''),
                                "final_url": fallback_url,
                                "is_fallback": True,
                                "original_domain": domain
                            }
                        else:
                            print(f"      ⚠️ Fallback insuffisant")
                    else:
                        print(f"      ❌ Fallback {response.status_code}")
                        
            except Exception as e:
                print(f"      ❌ Erreur fallback: {str(e)[:50]}")
        
        print(f"   ❌ Tous les fallbacks ont échoué pour {domain}")
        return None
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Résultat vide standardisé"""
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
            "content_quality": "failed",
            "final_url": "",
            "redirects_count": 0,
            "user_agent_used": ""
        }
    
    # Réutilisation des méthodes existantes (copier depuis valueserp_service.py)
    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace('www.', '')
        except:
            return ""
    
    # [Copier ici toutes les méthodes d'extraction existantes...]
    # _extract_content_with_trafilatura, _extract_metadata_with_trafilatura, etc.
    
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

# ... [Autres méthodes à copier depuis l'original]