#!/usr/bin/env python3
"""
Tests complets et intensifs de l'extraction trafilatura
"""

import asyncio
import time
from services.valueserp_service import ValueSerpService
from typing import List, Dict, Any
import statistics

class ComprehensiveExtractorTester:
    def __init__(self):
        self.service = ValueSerpService()
        self.results = []
    
    async def test_different_site_types(self):
        """Test 1: Différents types de sites web"""
        print("🔥 TEST 1: DIFFÉRENTS TYPES DE SITES WEB")
        print("=" * 70)
        
        test_sites = {
            "Actualités": [
                "https://www.lemonde.fr/politique/",
                "https://www.liberation.fr/",
                "https://www.lefigaro.fr/actualite-france/",
            ],
            "E-commerce": [
                "https://www.amazon.fr/",
                "https://www.fnac.com/",
                "https://www.cdiscount.com/",
            ],
            "Tech/Dev": [
                "https://stackoverflow.com/questions/tagged/python",
                "https://github.com/microsoft/vscode",
                "https://developer.mozilla.org/fr/docs/Web/JavaScript",
            ],
            "Education": [
                "https://fr.wikipedia.org/wiki/Machine_learning",
                "https://www.coursera.org/",
                "https://openclassrooms.com/fr/",
            ],
            "Blogs": [
                "https://medium.com/",
                "https://dev.to/",
                "https://blog.google/",
            ]
        }
        
        category_results = {}
        
        for category, urls in test_sites.items():
            print(f"\n📂 CATÉGORIE: {category}")
            print("-" * 40)
            
            category_stats = []
            
            for url in urls:
                try:
                    print(f"🔍 Test: {url}")
                    start_time = time.time()
                    
                    result = await self.service._fetch_page_content(url)
                    
                    extraction_time = time.time() - start_time
                    
                    stats = {
                        'url': url,
                        'word_count': result['word_count'],
                        'quality': result['content_quality'],
                        'time': round(extraction_time, 2),
                        'has_metadata': bool(result.get('author') or result.get('date')),
                        'html_elements': {
                            'images': result['images'],
                            'links': result['internal_links'] + result['external_links'],
                            'tables': result['tables'],
                        }
                    }
                    
                    category_stats.append(stats)
                    
                    print(f"   ✅ {stats['word_count']} mots, {stats['quality']}, {stats['time']}s")
                    if stats['has_metadata']:
                        print(f"   📊 Métadonnées: Auteur={result.get('author', 'N/A')}, Date={result.get('date', 'N/A')}")
                    
                except Exception as e:
                    print(f"   ❌ Erreur: {e}")
                    category_stats.append({
                        'url': url,
                        'word_count': 0,
                        'quality': 'failed',
                        'time': 0,
                        'error': str(e)
                    })
            
            # Statistiques par catégorie
            if category_stats:
                valid_stats = [s for s in category_stats if s['word_count'] > 0]
                if valid_stats:
                    avg_words = statistics.mean(s['word_count'] for s in valid_stats)
                    avg_time = statistics.mean(s['time'] for s in valid_stats)
                    success_rate = len(valid_stats) / len(category_stats) * 100
                    
                    print(f"\n📊 Stats {category}:")
                    print(f"   - Taux de succès: {success_rate:.1f}%")
                    print(f"   - Mots moyens: {avg_words:.0f}")
                    print(f"   - Temps moyen: {avg_time:.2f}s")
                    
                    category_results[category] = {
                        'success_rate': success_rate,
                        'avg_words': avg_words,
                        'avg_time': avg_time,
                        'details': category_stats
                    }
        
        return category_results
    
    async def test_robustness(self):
        """Test 2: Robustesse (sites cassés, timeouts, etc.)"""
        print("\n\n🛡️ TEST 2: ROBUSTESSE ET GESTION D'ERREURS")
        print("=" * 70)
        
        stress_urls = {
            "Sites lents": [
                "https://httpbin.org/delay/10",  # Timeout intentionnel
            ],
            "Sites inexistants": [
                "https://site-inexistant-123456.com/",
                "https://www.google.com/404-not-found",
            ],
            "HTML malformé": [
                "https://httpbin.org/html",  # HTML de test
            ],
            "Redirections": [
                "https://httpbin.org/redirect/3",  # Redirections multiples
            ],
            "Sites JavaScript-heavy": [
                "https://www.google.com/maps",  # SPA complexe
                "https://www.facebook.com/",   # JS lourd
            ]
        }
        
        robustness_results = {}
        
        for test_type, urls in stress_urls.items():
            print(f"\n🎯 TEST: {test_type}")
            print("-" * 30)
            
            for url in urls:
                try:
                    print(f"🔍 {url}")
                    start_time = time.time()
                    
                    # Test avec timeout réduit
                    result = await self.service._fetch_page_content(url)
                    
                    extraction_time = time.time() - start_time
                    
                    if result['word_count'] > 0:
                        print(f"   ✅ Réussi: {result['word_count']} mots, {extraction_time:.2f}s")
                    else:
                        print(f"   ⚠️ Vide mais pas d'erreur: {extraction_time:.2f}s")
                    
                except Exception as e:
                    print(f"   ❌ Erreur gérée: {str(e)[:100]}...")
                    
                    # Vérifier que l'erreur est bien gérée
                    robustness_results[url] = {
                        'error_handled': True,
                        'error_type': type(e).__name__
                    }
        
        return robustness_results
    
    async def test_performance(self):
        """Test 3: Performance et vitesse"""
        print("\n\n⚡ TEST 3: PERFORMANCE ET VITESSE")
        print("=" * 70)
        
        # Test sur sites rapides et connus
        fast_sites = [
            "https://httpbin.org/html",
            "https://example.com/",
            "https://www.python.org/",
            "https://docs.python.org/3/",
            "https://pypi.org/",
        ]
        
        times = []
        word_counts = []
        
        print("🏃‍♂️ Test de vitesse sur 5 sites...")
        
        overall_start = time.time()
        
        for i, url in enumerate(fast_sites, 1):
            try:
                print(f"🔍 {i}/5: {url}")
                
                start_time = time.time()
                result = await self.service._fetch_page_content(url)
                extraction_time = time.time() - start_time
                
                times.append(extraction_time)
                word_counts.append(result['word_count'])
                
                print(f"   ✅ {extraction_time:.2f}s → {result['word_count']} mots")
                
            except Exception as e:
                print(f"   ❌ {str(e)[:50]}...")
        
        overall_time = time.time() - overall_start
        
        if times:
            print(f"\n📊 STATISTIQUES DE PERFORMANCE:")
            print(f"   - Temps total: {overall_time:.2f}s")
            print(f"   - Temps moyen: {statistics.mean(times):.2f}s")
            print(f"   - Temps médian: {statistics.median(times):.2f}s")
            print(f"   - Plus rapide: {min(times):.2f}s")
            print(f"   - Plus lent: {max(times):.2f}s")
            print(f"   - Mots moyens: {statistics.mean(word_counts):.0f}")
            print(f"   - Débit: {sum(word_counts)/overall_time:.0f} mots/sec")
        
        return {
            'times': times,
            'word_counts': word_counts,
            'overall_time': overall_time,
            'throughput': sum(word_counts)/overall_time if overall_time > 0 else 0
        }
    
    async def test_seo_corpus(self):
        """Test 4: Corpus SEO réel"""
        print("\n\n🎯 TEST 4: CORPUS SEO RÉEL")
        print("=" * 70)
        
        seo_queries = [
            "agence seo paris",
            "consultant seo freelance", 
            "référencement naturel google",
            "audit seo gratuit",
            "formation seo en ligne"
        ]
        
        # Simulation de résultats SERP (URLs typiques du SEO)
        seo_urls = [
            "https://www.abondance.com/",
            "https://www.webrankinfo.com/",
            "https://blog.hubspot.fr/marketing",
            "https://www.journaldunet.com/web-tech/",
            "https://www.blogdumoderateur.com/",
        ]
        
        print("🎯 Test sur sites SEO typiques...")
        
        seo_results = []
        
        for url in seo_urls:
            try:
                print(f"🔍 {url}")
                
                result = await self.service._fetch_page_content(url)
                
                seo_analysis = {
                    'url': url,
                    'word_count': result['word_count'],
                    'quality': result['content_quality'],
                    'seo_metrics': {
                        'h1_present': bool(result.get('h1')),
                        'h1_length': len(result.get('h1', '')),
                        'meta_description': bool(result.get('description')),
                        'author_present': bool(result.get('author')),
                        'images': result['images'],
                        'internal_links': result['internal_links'],
                        'external_links': result['external_links'],
                        'content_structure_score': self._calculate_structure_score(result)
                    }
                }
                
                seo_results.append(seo_analysis)
                
                print(f"   ✅ {result['word_count']} mots, H1: {result.get('h1', 'N/A')[:50]}...")
                print(f"   📊 Score structure: {seo_analysis['seo_metrics']['content_structure_score']}/10")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        # Analyse globale SEO
        if seo_results:
            avg_words = statistics.mean(r['word_count'] for r in seo_results)
            h1_coverage = sum(1 for r in seo_results if r['seo_metrics']['h1_present']) / len(seo_results) * 100
            avg_structure = statistics.mean(r['seo_metrics']['content_structure_score'] for r in seo_results)
            
            print(f"\n📊 ANALYSE SEO GLOBALE:")
            print(f"   - Mots moyens: {avg_words:.0f}")
            print(f"   - Couverture H1: {h1_coverage:.0f}%")
            print(f"   - Score structure moyen: {avg_structure:.1f}/10")
        
        return seo_results
    
    def _calculate_structure_score(self, result: Dict[str, Any]) -> float:
        """Calcule un score de structure SEO sur 10"""
        score = 0
        
        # H1 présent et de bonne longueur
        if result.get('h1') and 10 <= len(result.get('h1', '')) <= 70:
            score += 2
        
        # Contenu suffisant
        if result['word_count'] >= 300:
            score += 2
        elif result['word_count'] >= 100:
            score += 1
        
        # Métadonnées présentes
        if result.get('author'):
            score += 1
        if result.get('date'):
            score += 1
        if result.get('description'):
            score += 1
        
        # Structure HTML
        if result['internal_links'] > 0:
            score += 1
        if result['images'] > 0:
            score += 1
        if result['tables'] > 0 or result['lists'] > 0:
            score += 1
        
        return min(score, 10)
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 LANCEMENT DES TESTS INTENSIFS TRAFILATURA")
        print("=" * 80)
        
        # Test 1: Types de sites
        site_results = await self.test_different_site_types()
        
        # Test 2: Robustesse
        robustness_results = await self.test_robustness()
        
        # Test 3: Performance
        perf_results = await self.test_performance()
        
        # Test 4: SEO
        seo_results = await self.test_seo_corpus()
        
        # Rapport final
        print("\n\n🏆 RAPPORT FINAL")
        print("=" * 80)
        
        print("📊 RÉSUMÉ GÉNÉRAL:")
        
        # Calcul du score global
        total_success_rate = 0
        total_categories = 0
        
        for category, data in site_results.items():
            if 'success_rate' in data:
                total_success_rate += data['success_rate']
                total_categories += 1
                print(f"   {category}: {data['success_rate']:.1f}% succès, {data['avg_words']:.0f} mots moy.")
        
        if total_categories > 0:
            overall_success = total_success_rate / total_categories
            print(f"\n🎯 TAUX DE SUCCÈS GLOBAL: {overall_success:.1f}%")
        
        if perf_results['times']:
            print(f"⚡ PERFORMANCE MOYENNE: {statistics.mean(perf_results['times']):.2f}s/page")
            print(f"🚀 DÉBIT GLOBAL: {perf_results['throughput']:.0f} mots/sec")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if overall_success >= 80:
            print("   ✅ Excellent! Extraction prête pour la production")
        elif overall_success >= 60:
            print("   ⚠️ Bon mais améliorations possibles")
        else:
            print("   ❌ Problèmes détectés, révision nécessaire")
        
        print("   🔧 Optimisations suggérées:")
        print("   - Cache intelligent pour éviter re-extractions")
        print("   - Timeout adaptatif selon le type de site")
        print("   - Parallélisation des requêtes")
        print("   - Fallback plus intelligent pour SPA")

async def main():
    tester = ComprehensiveExtractorTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())