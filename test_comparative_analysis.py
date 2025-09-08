#!/usr/bin/env python3
"""
Test comparatif : Ancien système vs Trafilatura
"""

import asyncio
import time
from services.valueserp_service import ValueSerpService
from bs4 import BeautifulSoup
import httpx
from typing import Dict, Any
import statistics

class ComparativeAnalyzer:
    def __init__(self):
        self.service = ValueSerpService()
    
    async def old_extraction_method(self, html_content: str) -> Dict[str, Any]:
        """Simule l'ancienne méthode d'extraction (sans trafilatura)"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ancienne méthode simplifiée (comme dans l'ancien code)
            for script in soup(["script", "style"]):
                script.decompose()
            
            for element in soup(["nav", "header", "footer", "aside"]):
                element.decompose()
            
            # Sélecteurs basiques de l'ancienne méthode
            main_selectors = ['main', 'article', '.main-content', '.content']
            
            for selector in main_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    content_text = main_element.get_text(separator=' ', strip=True)
                    word_count = len(content_text.split())
                    
                    if word_count >= 50:
                        return {
                            'content': content_text,
                            'word_count': word_count,
                            'method': 'old_selective',
                            'h1': soup.find('h1').get_text() if soup.find('h1') else '',
                            'quality': 'good' if word_count > 200 else 'acceptable'
                        }
            
            # Fallback agressif (ancienne méthode)
            body = soup.find('body')
            if body:
                body_text = body.get_text(separator=' ', strip=True)
                word_count = len(body_text.split())
                
                return {
                    'content': body_text,
                    'word_count': word_count,
                    'method': 'old_aggressive',
                    'h1': soup.find('h1').get_text() if soup.find('h1') else '',
                    'quality': 'poor' if word_count < 100 else 'acceptable'
                }
            
            return {
                'content': '',
                'word_count': 0,
                'method': 'old_failed',
                'h1': '',
                'quality': 'failed'
            }
            
        except Exception as e:
            return {
                'content': '',
                'word_count': 0,
                'method': 'old_error',
                'h1': '',
                'quality': 'error',
                'error': str(e)
            }
    
    async def compare_extractions(self, url: str) -> Dict[str, Any]:
        """Compare l'ancienne et nouvelle méthode sur une URL"""
        
        print(f"🔍 Analyse comparative: {url}")
        
        try:
            # Récupération HTML commune
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code != 200:
                    return {
                        'url': url,
                        'status': 'failed',
                        'error': f'HTTP {response.status_code}'
                    }
                
                html_content = response.text
            
            # Test ancienne méthode
            start_time = time.time()
            old_result = await self.old_extraction_method(html_content)
            old_time = time.time() - start_time
            
            # Test nouvelle méthode (trafilatura)
            start_time = time.time()
            new_result = self.service._extract_content_with_trafilatura(html_content, url)
            new_time = time.time() - start_time
            
            # Métadonnées avec trafilatura
            metadata = self.service._extract_metadata_with_trafilatura(html_content)
            
            # Analyse comparative
            comparison = {
                'url': url,
                'old_method': {
                    'word_count': old_result['word_count'],
                    'quality': old_result['quality'],
                    'method_used': old_result['method'],
                    'time': round(old_time, 3),
                    'h1': old_result['h1'][:100] if old_result['h1'] else '',
                    'content_preview': old_result['content'][:200] if old_result['content'] else ''
                },
                'new_method': {
                    'word_count': len(new_result.split()) if new_result else 0,
                    'quality': self.service._validate_content_quality_v2(new_result, len(new_result.split()) if new_result else 0, metadata),
                    'time': round(new_time, 3),
                    'h1': metadata.get('title', '')[:100],
                    'author': metadata.get('author', ''),
                    'date': metadata.get('date', ''),
                    'content_preview': new_result[:200] if new_result else ''
                }
            }
            
            # Calcul des améliorations
            old_words = comparison['old_method']['word_count']
            new_words = comparison['new_method']['word_count']
            
            comparison['improvement'] = {
                'word_count_gain': new_words - old_words,
                'word_count_ratio': round(new_words / old_words, 2) if old_words > 0 else float('inf'),
                'time_improvement': old_time - new_time,
                'metadata_added': bool(metadata.get('author') or metadata.get('date')),
                'quality_upgrade': self._compare_quality(old_result['quality'], comparison['new_method']['quality'])
            }
            
            return comparison
            
        except Exception as e:
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    def _compare_quality(self, old_quality: str, new_quality: str) -> str:
        """Compare les niveaux de qualité"""
        quality_scores = {
            'failed': 0, 'error': 0, 'empty': 0,
            'too_short': 1, 'poor': 2, 'short': 3,
            'acceptable': 4, 'good': 5, 'excellent': 6,
            'comprehensive': 7, 'professional': 8
        }
        
        old_score = quality_scores.get(old_quality, 0)
        new_score = quality_scores.get(new_quality, 0)
        
        if new_score > old_score:
            return 'upgraded'
        elif new_score == old_score:
            return 'same'
        else:
            return 'downgraded'
    
    async def run_comparative_analysis(self):
        """Lance l'analyse comparative complète"""
        
        print("🔥 ANALYSE COMPARATIVE : ANCIEN vs TRAFILATURA")
        print("=" * 80)
        
        # Sites de test variés
        test_urls = [
            "https://fr.wikipedia.org/wiki/Python_(langage)",
            "https://stackoverflow.com/questions/tagged/python",
            "https://www.python.org/",
            "https://docs.python.org/3/",
            "https://github.com/python/cpython",
            "https://pypi.org/project/requests/",
            "https://developer.mozilla.org/fr/docs/Web/JavaScript",
            "https://www.webrankinfo.com/",
        ]
        
        results = []
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n🧪 TEST {i}/{len(test_urls)}")
            print("-" * 50)
            
            result = await self.compare_extractions(url)
            
            if result.get('status') == 'error':
                print(f"❌ Erreur: {result['error']}")
                continue
            elif result.get('status') == 'failed':
                print(f"⚠️ Échec: {result['error']}")
                continue
            
            results.append(result)
            
            # Affichage des résultats
            old = result['old_method']
            new = result['new_method']
            imp = result['improvement']
            
            print(f"📊 ANCIEN SYSTÈME:")
            print(f"   - Mots extraits: {old['word_count']}")
            print(f"   - Qualité: {old['quality']}")
            print(f"   - Temps: {old['time']}s")
            print(f"   - Méthode: {old['method_used']}")
            
            print(f"🚀 TRAFILATURA:")
            print(f"   - Mots extraits: {new['word_count']}")
            print(f"   - Qualité: {new['quality']}")
            print(f"   - Temps: {new['time']}s")
            print(f"   - Auteur: {new['author'] or 'N/A'}")
            print(f"   - Date: {new['date'] or 'N/A'}")
            
            print(f"📈 AMÉLIORATIONS:")
            print(f"   - Gain de mots: +{imp['word_count_gain']} ({imp['word_count_ratio']}x)")
            print(f"   - Gain de temps: {imp['time_improvement']:+.3f}s")
            print(f"   - Métadonnées: {'✅' if imp['metadata_added'] else '❌'}")
            print(f"   - Qualité: {imp['quality_upgrade']}")
        
        # Statistiques globales
        if results:
            self._generate_global_stats(results)
    
    def _generate_global_stats(self, results):
        """Génère les statistiques globales"""
        
        print(f"\n\n📊 STATISTIQUES GLOBALES ({len(results)} sites testés)")
        print("=" * 80)
        
        # Calculs statistiques
        old_words = [r['old_method']['word_count'] for r in results]
        new_words = [r['new_method']['word_count'] for r in results]
        word_gains = [r['improvement']['word_count_gain'] for r in results]
        time_gains = [r['improvement']['time_improvement'] for r in results]
        
        quality_upgrades = sum(1 for r in results if r['improvement']['quality_upgrade'] == 'upgraded')
        metadata_additions = sum(1 for r in results if r['improvement']['metadata_added'])
        
        print(f"📈 EXTRACTION DE CONTENU:")
        print(f"   - Mots moyens (ancien): {statistics.mean(old_words):.0f}")
        print(f"   - Mots moyens (trafilatura): {statistics.mean(new_words):.0f}")
        print(f"   - Gain moyen: +{statistics.mean(word_gains):.0f} mots")
        print(f"   - Ratio moyen: {statistics.mean(new_words)/statistics.mean(old_words):.1f}x")
        
        print(f"⚡ PERFORMANCE:")
        print(f"   - Gain de temps moyen: {statistics.mean(time_gains):+.3f}s")
        print(f"   - Sites plus rapides: {sum(1 for t in time_gains if t > 0)}/{len(results)}")
        
        print(f"🎯 QUALITÉ:")
        print(f"   - Améliorations qualité: {quality_upgrades}/{len(results)} ({quality_upgrades/len(results)*100:.1f}%)")
        print(f"   - Métadonnées ajoutées: {metadata_additions}/{len(results)} ({metadata_additions/len(results)*100:.1f}%)")
        
        # Évaluation finale
        overall_improvement = statistics.mean([
            r['improvement']['word_count_ratio'] for r in results 
            if r['improvement']['word_count_ratio'] != float('inf')
        ])
        
        print(f"\n🏆 ÉVALUATION FINALE:")
        if overall_improvement >= 2.0:
            print(f"   🚀 EXCELLENT: {overall_improvement:.1f}x d'amélioration moyenne")
            print("   Trafilatura transforme complètement votre extraction!")
        elif overall_improvement >= 1.5:
            print(f"   ✅ TRÈS BON: {overall_improvement:.1f}x d'amélioration moyenne")
            print("   Gain significatif avec trafilatura")
        elif overall_improvement >= 1.2:
            print(f"   👍 BON: {overall_improvement:.1f}x d'amélioration moyenne")
            print("   Amélioration notable")
        else:
            print(f"   ⚠️ MITIGÉ: {overall_improvement:.1f}x d'amélioration moyenne")
            print("   Bénéfices limités sur ce corpus")
        
        print(f"\n💡 RECOMMANDATIONS:")
        print("   ✅ Déployer trafilatura en production")
        print("   ✅ Supprimer l'ancien code d'extraction")
        print("   ✅ Monitorer la qualité en continu")
        print("   🚀 Considérer l'ajout de cache intelligent")

async def main():
    analyzer = ComparativeAnalyzer()
    await analyzer.run_comparative_analysis()

if __name__ == "__main__":
    asyncio.run(main())