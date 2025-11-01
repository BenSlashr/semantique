#!/usr/bin/env python3
"""
Test de l'outil d'extraction sur des requêtes Google réelles
"""

import asyncio
from services.valueserp_service import ValueSerpService
from services.seo_analyzer import SEOAnalyzer
from collections import Counter
import time

class GoogleQueryTester:
    def __init__(self):
        self.valueserp_service = ValueSerpService()
        self.seo_analyzer = SEOAnalyzer()
    
    async def test_query_complete(self, query: str, location: str = "France", language: str = "fr"):
        """Test complet d'une requête : SERP + extraction + analyse"""
        
        print(f"\n{'='*80}")
        print(f"🔍 TEST REQUÊTE: '{query}'")
        print(f"📍 Localisation: {location}")
        print(f"🗣️ Langue: {language}")
        print(f"{'='*80}")
        
        try:
            start_time = time.time()
            
            # ÉTAPE 1: Récupération SERP
            print(f"\n📡 ÉTAPE 1: Récupération des résultats SERP...")
            serp_results = await self.valueserp_service.get_serp_data(query, location, language)
            serp_time = time.time() - start_time
            
            if not serp_results or not serp_results.get('organic_results'):
                print(f"❌ Aucun résultat SERP trouvé pour '{query}'")
                return None
            
            organic_results = serp_results.get('organic_results', [])
            paa_questions = serp_results.get('paa', [])
            related_searches = serp_results.get('related_searches', [])
            
            print(f"✅ SERP récupérés: {len(organic_results)} résultats organiques")
            print(f"   📋 PAA: {len(paa_questions)} questions")
            print(f"   🔗 Recherches associées: {len(related_searches)}")
            print(f"   ⏱️ Temps SERP: {serp_time:.2f}s")
            
            # ÉTAPE 2: Extraction des contenus
            print(f"\n📄 ÉTAPE 2: Extraction des contenus des concurrents...")
            extraction_start = time.time()
            
            successful_extractions = []
            failed_extractions = []
            
            for i, result in enumerate(organic_results[:5], 1):  # Top 5 seulement
                print(f"\n   🔍 [{i}/5] {result['domain']}")
                print(f"      URL: {result['url']}")
                print(f"      Titre: {result['title'][:80]}...")
                
                try:
                    content_data = await self.valueserp_service._fetch_page_content(result['url'])
                    
                    if content_data['word_count'] > 0:
                        successful_extractions.append({
                            'position': result['position'],
                            'domain': result['domain'],
                            'url': result['url'],
                            'title': result['title'],
                            'word_count': content_data['word_count'],
                            'quality': content_data['content_quality'],
                            'content': content_data['content'],
                            'h1': content_data.get('h1', ''),
                            'author': content_data.get('author', ''),
                            'images': content_data['images'],
                            'links': content_data['internal_links'] + content_data['external_links']
                        })
                        print(f"      ✅ Extrait: {content_data['word_count']} mots, qualité: {content_data['content_quality']}")
                    else:
                        failed_extractions.append({
                            'domain': result['domain'],
                            'url': result['url'],
                            'reason': 'Aucun contenu extrait'
                        })
                        print(f"      ❌ Échec: Aucun contenu extrait")
                        
                except Exception as e:
                    failed_extractions.append({
                        'domain': result['domain'], 
                        'url': result['url'],
                        'reason': str(e)
                    })
                    print(f"      ❌ Erreur: {str(e)[:100]}...")
            
            extraction_time = time.time() - extraction_start
            print(f"\n   📊 Bilan extraction:")
            print(f"      ✅ Réussies: {len(successful_extractions)}/5")
            print(f"      ❌ Échouées: {len(failed_extractions)}/5")
            print(f"      ⏱️ Temps extraction: {extraction_time:.2f}s")
            
            # ÉTAPE 3: Analyse sémantique globale
            print(f"\n🧠 ÉTAPE 3: Analyse sémantique des contenus...")
            analysis_start = time.time()
            
            # Concaténation de tous les contenus pour analyse
            all_content = " ".join([extract['content'] for extract in successful_extractions])
            total_words = sum([extract['word_count'] for extract in successful_extractions])
            
            if all_content:
                # Analyse des mots-clés sur l'ensemble des contenus
                semantic_analysis = self._analyze_semantic_field(all_content, query)
                
                analysis_time = time.time() - analysis_start
                print(f"   ✅ Analyse terminée en {analysis_time:.2f}s")
                print(f"   📝 Corpus analysé: {total_words} mots au total")
                
                # ÉTAPE 4: Génération du rapport
                total_time = time.time() - start_time
                
                report = {
                    'query': query,
                    'location': location,
                    'language': language,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'serp_data': {
                        'organic_count': len(organic_results),
                        'paa_count': len(paa_questions),
                        'related_searches_count': len(related_searches),
                        'paa_questions': paa_questions[:10],  # Top 10
                        'related_searches': related_searches[:10]
                    },
                    'extraction_data': {
                        'successful_count': len(successful_extractions),
                        'failed_count': len(failed_extractions),
                        'total_words': total_words,
                        'successful_extractions': successful_extractions,
                        'failed_extractions': failed_extractions
                    },
                    'semantic_analysis': semantic_analysis,
                    'performance': {
                        'serp_time': round(serp_time, 2),
                        'extraction_time': round(extraction_time, 2),
                        'analysis_time': round(analysis_time, 2),
                        'total_time': round(total_time, 2)
                    }
                }
                
                self._display_report(report)
                return report
                
            else:
                print(f"❌ Aucun contenu à analyser")
                return None
                
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return None
    
    def _analyze_semantic_field(self, content: str, query: str) -> dict:
        """Analyse sémantique du corpus de contenu"""
        
        # Nettoyage et tokenisation
        import re
        clean_content = re.sub(r'[^\w\s\'-]', ' ', content.lower())
        words = clean_content.split()
        
        # Mots-clés de la requête
        query_words = set(query.lower().split())
        
        # Stop words français basiques
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'à', 'ce', 'se',
            'que', 'qui', 'dont', 'où', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'pour', 'par', 'avec', 'sans', 'dans', 'sur', 'sous', 'vers', 'entre',
            'plus', 'moins', 'très', 'bien', 'mal', 'tout', 'tous', 'avoir', 'être',
            'faire', 'dire', 'aller', 'voir', 'savoir', 'pouvoir', 'vouloir'
        }
        
        # Filtrage des mots significatifs
        meaningful_words = [
            word for word in words 
            if len(word) >= 3 
            and word not in stop_words
            and not word.isdigit()
            and word.isalpha()
        ]
        
        # Comptage des fréquences
        word_freq = Counter(meaningful_words)
        
        # Mots liés à la requête (contiennent un mot de la requête)
        related_words = {}
        for word, freq in word_freq.most_common(100):
            for query_word in query_words:
                if query_word in word or word in query_word:
                    related_words[word] = freq
                    break
        
        # Bi-grammes significatifs
        bigrams = []
        for i in range(len(meaningful_words) - 1):
            if (meaningful_words[i] not in stop_words and 
                meaningful_words[i+1] not in stop_words):
                bigram = f"{meaningful_words[i]} {meaningful_words[i+1]}"
                bigrams.append(bigram)
        
        bigram_freq = Counter(bigrams)
        
        return {
            'total_meaningful_words': len(meaningful_words),
            'unique_words': len(set(meaningful_words)),
            'vocabulary_richness': len(set(meaningful_words)) / len(meaningful_words) if meaningful_words else 0,
            'top_words': word_freq.most_common(20),
            'query_related_words': list(related_words.items())[:15],
            'top_bigrams': bigram_freq.most_common(10),
            'query_coverage': len(related_words) / len(query_words) if query_words else 0
        }
    
    def _display_report(self, report: dict):
        """Affiche le rapport d'analyse complet"""
        
        print(f"\n{'='*80}")
        print(f"📊 RAPPORT FINAL - '{report['query']}'")
        print(f"{'='*80}")
        
        # Performance
        perf = report['performance']
        print(f"\n⚡ PERFORMANCE:")
        print(f"   ⏱️ Temps total: {perf['total_time']}s")
        print(f"   📡 SERP: {perf['serp_time']}s")
        print(f"   📄 Extraction: {perf['extraction_time']}s") 
        print(f"   🧠 Analyse: {perf['analysis_time']}s")
        
        # Données SERP
        serp = report['serp_data']
        print(f"\n📡 DONNÉES SERP:")
        print(f"   📝 Résultats organiques: {serp['organic_count']}")
        print(f"   ❓ Questions PAA: {serp['paa_count']}")
        print(f"   🔗 Recherches associées: {serp['related_searches_count']}")
        
        if serp['paa_questions']:
            print(f"\n   🔝 TOP QUESTIONS PAA:")
            for i, question in enumerate(serp['paa_questions'][:5], 1):
                print(f"      {i}. {question}")
        
        if serp['related_searches']:
            print(f"\n   🔝 TOP RECHERCHES ASSOCIÉES:")
            for i, search in enumerate(serp['related_searches'][:5], 1):
                print(f"      {i}. {search}")
        
        # Extraction
        extract = report['extraction_data']
        print(f"\n📄 EXTRACTION CONTENU:")
        print(f"   ✅ Réussies: {extract['successful_count']}/5")
        print(f"   📝 Mots totaux: {extract['total_words']:,}")
        print(f"   📊 Moyenne: {extract['total_words'] // max(extract['successful_count'], 1):,} mots/site")
        
        print(f"\n   🏆 TOP SITES ANALYSÉS:")
        for site in extract['successful_extractions']:
            print(f"      #{site['position']} {site['domain']:<25} {site['word_count']:>5} mots ({site['quality']})")
        
        if extract['failed_extractions']:
            print(f"\n   ❌ ÉCHECS D'EXTRACTION:")
            for fail in extract['failed_extractions'][:3]:
                print(f"      - {fail['domain']}: {fail['reason'][:50]}...")
        
        # Analyse sémantique
        sem = report['semantic_analysis']
        print(f"\n🧠 ANALYSE SÉMANTIQUE:")
        print(f"   📝 Mots significatifs: {sem['total_meaningful_words']:,}")
        print(f"   💎 Mots uniques: {sem['unique_words']:,}")
        print(f"   📊 Richesse vocabulaire: {sem['vocabulary_richness']:.2f}")
        print(f"   🎯 Couverture requête: {sem['query_coverage']:.1%}")
        
        print(f"\n   🔝 TOP 15 MOTS-CLÉS:")
        for i, (word, freq) in enumerate(sem['top_words'][:15], 1):
            print(f"      {i:2}. {word:<20} ({freq:>3}x)")
        
        if sem['query_related_words']:
            print(f"\n   🎯 MOTS LIÉS À LA REQUÊTE:")
            for word, freq in sem['query_related_words'][:10]:
                print(f"      • {word:<20} ({freq:>3}x)")
        
        print(f"\n   🔗 TOP EXPRESSIONS:")
        for i, (bigram, freq) in enumerate(sem['top_bigrams'][:8], 1):
            print(f"      {i}. \"{bigram}\" ({freq}x)")
    
    async def test_multiple_queries(self):
        """Test sur les 3 requêtes demandées"""
        
        queries = [
            "nettoyage après inondation",
            "etat surface acier", 
            "aide implantation"
        ]
        
        print("🚀 TEST DE L'OUTIL D'EXTRACTION SUR REQUÊTES GOOGLE RÉELLES")
        print("=" * 80)
        
        all_reports = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n\n🎯 REQUÊTE {i}/{len(queries)}")
            report = await self.test_query_complete(query)
            
            if report:
                all_reports.append(report)
            
            if i < len(queries):
                print(f"\n⏳ Pause de 2 secondes avant requête suivante...")
                await asyncio.sleep(2)
        
        # Comparaison finale
        if len(all_reports) > 1:
            self._compare_queries(all_reports)
        
        return all_reports
    
    def _compare_queries(self, reports):
        """Comparaison entre toutes les requêtes testées"""
        
        print(f"\n{'='*80}")
        print(f"🆚 COMPARAISON GLOBALE DES REQUÊTES")
        print(f"{'='*80}")
        
        print(f"{'Requête':<30} {'Mots':<8} {'Sites':<6} {'Temps':<6} {'PAA':<4}")
        print("-" * 60)
        
        for report in reports:
            query = report['query'][:28]
            total_words = report['extraction_data']['total_words']
            successful = report['extraction_data']['successful_count']
            total_time = report['performance']['total_time']
            paa_count = report['serp_data']['paa_count']
            
            print(f"{query:<30} {total_words:<8,} {successful:<6} {total_time:<6.1f} {paa_count:<4}")
        
        # Analyse comparative
        print(f"\n💡 INSIGHTS:")
        
        # Requête avec le plus de contenu
        max_words_report = max(reports, key=lambda r: r['extraction_data']['total_words'])
        print(f"   📈 Plus de contenu: '{max_words_report['query']}' ({max_words_report['extraction_data']['total_words']:,} mots)")
        
        # Requête la plus rapide
        fastest_report = min(reports, key=lambda r: r['performance']['total_time'])
        print(f"   ⚡ Plus rapide: '{fastest_report['query']}' ({fastest_report['performance']['total_time']:.1f}s)")
        
        # Meilleur taux de succès extraction
        best_success_report = max(reports, key=lambda r: r['extraction_data']['successful_count'])
        print(f"   🎯 Meilleur taux succès: '{best_success_report['query']}' ({best_success_report['extraction_data']['successful_count']}/5 sites)")

async def main():
    tester = GoogleQueryTester()
    await tester.test_multiple_queries()

if __name__ == "__main__":
    asyncio.run(main())