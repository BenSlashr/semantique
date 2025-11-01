#!/usr/bin/env python3
"""
Debug et test des paramètres de sévérité d'extraction
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.settings import use_config

class ExtractionSeverityDebugger:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    async def debug_extraction_methods(self, url: str):
        """Teste toutes les méthodes d'extraction sur une URL"""
        
        print(f"🔧 DEBUG EXTRACTION - {url}")
        print("=" * 80)
        
        try:
            # Récupération HTML
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers={'User-Agent': self.user_agent})
                html_content = response.text
            
            print(f"✅ HTML récupéré: {len(html_content)} caractères")
            
            # MÉTHODE 1: Trafilatura par défaut (actuelle)
            print(f"\n🔬 MÉTHODE 1: Trafilatura par défaut")
            result1 = self.extract_trafilatura_default(html_content, url)
            
            # MÉTHODE 2: Trafilatura mode permissif
            print(f"\n🔬 MÉTHODE 2: Trafilatura mode permissif")  
            result2 = self.extract_trafilatura_permissive(html_content, url)
            
            # MÉTHODE 3: Trafilatura mode agressif
            print(f"\n🔬 MÉTHODE 3: Trafilatura mode agressif")
            result3 = self.extract_trafilatura_aggressive(html_content, url)
            
            # MÉTHODE 4: BeautifulSoup classique
            print(f"\n🔬 MÉTHODE 4: BeautifulSoup classique")
            result4 = self.extract_beautifulsoup(html_content)
            
            # MÉTHODE 5: BeautifulSoup agressif
            print(f"\n🔬 MÉTHODE 5: BeautifulSoup agressif")
            result5 = self.extract_beautifulsoup_aggressive(html_content)
            
            # Comparaison
            self.compare_results([
                ("Trafilatura défaut", result1),
                ("Trafilatura permissif", result2), 
                ("Trafilatura agressif", result3),
                ("BeautifulSoup classique", result4),
                ("BeautifulSoup agressif", result5)
            ])
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    def extract_trafilatura_default(self, html_content: str, url: str) -> dict:
        """Méthode trafilatura actuelle (restrictive)"""
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
                favor_precision=True  # RESTRICTIF
            )
            
            return {
                'content': content or '',
                'word_count': len(content.split()) if content else 0,
                'method': 'trafilatura_default'
            }
        except Exception as e:
            return {'content': '', 'word_count': 0, 'error': str(e)}
    
    def extract_trafilatura_permissive(self, html_content: str, url: str) -> dict:
        """Trafilatura plus permissif"""
        try:
            config = use_config()
            config.set('DEFAULT', 'EXTRACTION_TIMEOUT', '30')
            # Paramètres plus permissifs
            config.set('DEFAULT', 'MIN_EXTRACTED_SIZE', '25')  # Plus petit minimum
            config.set('DEFAULT', 'MIN_OUTPUT_SIZE', '25')
            
            content = trafilatura.extract(
                html_content,
                url=url,
                config=config,
                include_comments=False,
                include_tables=True,
                include_links=True,  # INCLURE LIENS
                include_images=False,
                include_formatting=True,  # INCLURE FORMAT
                output_format='txt',
                target_language=None,  # PAS DE FILTRE LANGUE
                deduplicate=False,  # PAS DE DÉDUP
                favor_precision=False,  # PRIVILÉGIER RAPPEL
                favor_recall=True
            )
            
            return {
                'content': content or '',
                'word_count': len(content.split()) if content else 0,
                'method': 'trafilatura_permissive'
            }
        except Exception as e:
            return {'content': '', 'word_count': 0, 'error': str(e)}
    
    def extract_trafilatura_aggressive(self, html_content: str, url: str) -> dict:
        """Trafilatura mode très agressif"""
        try:
            content = trafilatura.extract(
                html_content,
                url=url,
                include_comments=True,   # TOUT INCLURE
                include_tables=True,
                include_links=True,
                include_images=True,
                include_formatting=True,
                output_format='txt',
                target_language=None,
                deduplicate=False,
                favor_precision=False,
                favor_recall=True,
                only_with_metadata=False  # PAS DE FILTRE METADATA
            )
            
            return {
                'content': content or '',
                'word_count': len(content.split()) if content else 0,
                'method': 'trafilatura_aggressive'
            }
        except Exception as e:
            return {'content': '', 'word_count': 0, 'error': str(e)}
    
    def extract_beautifulsoup(self, html_content: str) -> dict:
        """BeautifulSoup méthode classique"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Supprime scripts et styles
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Cherche contenu principal
            main_selectors = ['main', 'article', '[role="main"]', '.main-content', '.content']
            
            for selector in main_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    content = main_element.get_text(separator=' ', strip=True)
                    if len(content.split()) >= 20:
                        return {
                            'content': content,
                            'word_count': len(content.split()),
                            'method': 'beautifulsoup_selective'
                        }
            
            # Fallback body
            body = soup.find('body')
            if body:
                content = body.get_text(separator=' ', strip=True)
                return {
                    'content': content,
                    'word_count': len(content.split()),
                    'method': 'beautifulsoup_body'
                }
            
            return {'content': '', 'word_count': 0, 'method': 'beautifulsoup_failed'}
            
        except Exception as e:
            return {'content': '', 'word_count': 0, 'error': str(e)}
    
    def extract_beautifulsoup_aggressive(self, html_content: str) -> dict:
        """BeautifulSoup très agressif"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Supprime seulement le minimum
            for element in soup(['script', 'style']):
                element.decompose()
            
            # Prend tout le body
            body = soup.find('body')
            if body:
                content = body.get_text(separator=' ', strip=True)
                # Nettoie un peu
                words = content.split()
                # Supprime les mots trop courts/longs
                clean_words = [w for w in words if 2 <= len(w) <= 50]
                clean_content = ' '.join(clean_words)
                
                return {
                    'content': clean_content,
                    'word_count': len(clean_words),
                    'method': 'beautifulsoup_aggressive'
                }
            
            return {'content': '', 'word_count': 0, 'method': 'beautifulsoup_no_body'}
            
        except Exception as e:
            return {'content': '', 'word_count': 0, 'error': str(e)}
    
    def compare_results(self, results):
        """Compare les résultats des différentes méthodes"""
        
        print(f"\n📊 COMPARAISON DES MÉTHODES")
        print("=" * 80)
        
        for method_name, result in results:
            word_count = result.get('word_count', 0)
            error = result.get('error')
            
            if error:
                print(f"❌ {method_name:<25}: ERREUR - {error}")
            else:
                print(f"📝 {method_name:<25}: {word_count:>5} mots")
                
                # Aperçu du contenu
                content = result.get('content', '')
                if content:
                    preview = content[:100].replace('\n', ' ').strip()
                    print(f"   Aperçu: {preview}...")
        
        # Recommandations
        print(f"\n💡 ANALYSE:")
        
        word_counts = [r[1].get('word_count', 0) for r in results if not r[1].get('error')]
        
        if word_counts:
            max_words = max(word_counts)
            max_method = [r[0] for r in results if r[1].get('word_count') == max_words][0]
            
            print(f"   🏆 Méthode avec le plus de contenu: {max_method} ({max_words} mots)")
            
            # Calcul des ratios
            default_words = results[0][1].get('word_count', 1)  # Trafilatura défaut
            
            for method_name, result in results[1:]:
                if not result.get('error'):
                    ratio = result.get('word_count', 0) / max(default_words, 1)
                    print(f"   📈 {method_name} vs défaut: {ratio:.1f}x")

async def main():
    debugger = ExtractionSeverityDebugger()
    
    # Test sur le site problématique
    url = "https://agence-slashr.fr/"
    await debugger.debug_extraction_methods(url)

if __name__ == "__main__":
    asyncio.run(main())