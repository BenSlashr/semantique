#!/usr/bin/env python3
"""
Test manuel avec URLs réelles du TOP 5 des requêtes demandées
"""

import asyncio
from services.valueserp_service import ValueSerpService
from collections import Counter
import time

class ManualSerpTester:
    def __init__(self):
        self.service = ValueSerpService()
    
    async def test_query_manual(self, query: str, top_urls: list):
        """Test avec URLs manuelles du top 5"""
        
        print(f"\n{'='*80}")
        print(f"🔍 TEST REQUÊTE MANUELLE: '{query}'")
        print(f"📍 URLs simulées du TOP 5 Google")
        print(f"{'='*80}")
        
        results = {
            'query': query,
            'extractions': [],
            'failed': [],
            'stats': {}
        }
        
        print(f"\n📄 EXTRACTION DES CONTENUS TOP 5:")
        
        for i, url in enumerate(top_urls[:5], 1):
            print(f"\n   🔍 [{i}/5] Analyse de: {url}")
            
            try:
                start_time = time.time()
                content_data = await self.service._fetch_page_content(url)
                extraction_time = time.time() - start_time
                
                if content_data['word_count'] > 0:
                    extraction = {
                        'position': i,
                        'url': url,
                        'domain': self._extract_domain(url),
                        'word_count': content_data['word_count'],
                        'quality': content_data['content_quality'],
                        'content': content_data['content'],
                        'h1': content_data.get('h1', ''),
                        'author': content_data.get('author', ''),
                        'date': content_data.get('date', ''),
                        'images': content_data['images'],
                        'links': content_data['internal_links'] + content_data['external_links'],
                        'extraction_time': round(extraction_time, 2)
                    }
                    
                    results['extractions'].append(extraction)
                    
                    print(f"      ✅ Succès: {content_data['word_count']} mots ({content_data['content_quality']})")
                    print(f"      📄 H1: {content_data.get('h1', 'N/A')[:60]}...")
                    print(f"      ⏱️ Temps: {extraction_time:.2f}s")
                    
                    if content_data.get('author'):
                        print(f"      👤 Auteur: {content_data['author']}")
                    if content_data.get('date'):
                        print(f"      📅 Date: {content_data['date']}")
                else:
                    results['failed'].append({
                        'url': url,
                        'reason': 'Aucun contenu extrait'
                    })
                    print(f"      ❌ Échec: Aucun contenu extrait")
                    
            except Exception as e:
                results['failed'].append({
                    'url': url,
                    'reason': str(e)
                })
                print(f"      ❌ Erreur: {str(e)[:80]}...")
        
        # Analyse des mots-clés
        if results['extractions']:
            self._analyze_extractions(results)
        
        self._display_summary(results)
        return results
    
    def _extract_domain(self, url):
        """Extrait le domaine d'une URL"""
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc.replace('www.', '')
        except:
            return url
    
    def _analyze_extractions(self, results):
        """Analyse sémantique des extractions"""
        
        # Concaténation de tous les contenus
        all_content = " ".join([ext['content'] for ext in results['extractions']])
        query = results['query']
        
        # Analyse basique des mots-clés
        import re
        clean_content = re.sub(r'[^\w\s\'-]', ' ', all_content.lower())
        words = [word for word in clean_content.split() if len(word) >= 3]
        
        # Stop words français
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'à', 'ce', 'se',
            'que', 'qui', 'dont', 'où', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'on',
            'pour', 'par', 'avec', 'sans', 'dans', 'sur', 'sous', 'vers', 'entre', 'chez',
            'plus', 'moins', 'très', 'bien', 'mal', 'tout', 'tous', 'avoir', 'être', 'faire',
            'dire', 'aller', 'voir', 'savoir', 'pouvoir', 'vouloir', 'venir', 'falloir',
            'depuis', 'pendant', 'après', 'avant', 'encore', 'déjà', 'toujours', 'jamais'
        }
        
        meaningful_words = [word for word in words if word not in stop_words and word.isalpha()]
        word_freq = Counter(meaningful_words)
        
        # Mots liés à la requête
        query_words = set(query.lower().split())
        related_words = {}
        for word, freq in word_freq.most_common(50):
            for query_word in query_words:
                if query_word in word or word in query_word or len(query_word) > 4 and query_word[:4] in word:
                    related_words[word] = freq
                    break
        
        # Bi-grammes
        bigrams = []
        for i in range(len(meaningful_words) - 1):
            bigram = f"{meaningful_words[i]} {meaningful_words[i+1]}"
            bigrams.append(bigram)
        
        bigram_freq = Counter(bigrams)
        
        results['analysis'] = {
            'total_words': len(words),
            'meaningful_words': len(meaningful_words),
            'unique_words': len(set(meaningful_words)),
            'top_words': word_freq.most_common(20),
            'query_related': list(related_words.items())[:15],
            'top_bigrams': bigram_freq.most_common(10)
        }
    
    def _display_summary(self, results):
        """Affiche le résumé des résultats"""
        
        print(f"\n{'='*80}")
        print(f"📊 RÉSUMÉ - '{results['query']}'")
        print(f"{'='*80}")
        
        successful = len(results['extractions'])
        failed = len(results['failed'])
        total_words = sum([ext['word_count'] for ext in results['extractions']])
        
        print(f"\n📈 STATISTIQUES EXTRACTION:")
        print(f"   ✅ Réussies: {successful}/5")
        print(f"   ❌ Échouées: {failed}/5")
        print(f"   📝 Mots totaux: {total_words:,}")
        print(f"   📊 Moyenne: {total_words // max(successful, 1):,} mots/site")
        
        if results['extractions']:
            print(f"\n🏆 CLASSEMENT DES SITES:")
            for ext in sorted(results['extractions'], key=lambda x: x['word_count'], reverse=True):
                print(f"   #{ext['position']} {ext['domain']:<30} {ext['word_count']:>5,} mots ({ext['quality']})")
        
        if 'analysis' in results:
            analysis = results['analysis']
            print(f"\n🧠 ANALYSE SÉMANTIQUE:")
            print(f"   📝 Mots significatifs: {analysis['meaningful_words']:,}")
            print(f"   💎 Mots uniques: {analysis['unique_words']:,}")
            print(f"   📊 Richesse: {analysis['unique_words']/max(analysis['meaningful_words'],1):.2f}")
            
            print(f"\n   🔝 TOP 15 MOTS-CLÉS:")
            for i, (word, freq) in enumerate(analysis['top_words'][:15], 1):
                print(f"      {i:2}. {word:<20} ({freq:>3}x)")
            
            if analysis['query_related']:
                print(f"\n   🎯 MOTS LIÉS À '{results['query']}':")
                for word, freq in analysis['query_related'][:10]:
                    print(f"      • {word:<20} ({freq:>3}x)")
            
            print(f"\n   🔗 TOP EXPRESSIONS:")
            for i, (bigram, freq) in enumerate(analysis['top_bigrams'][:8], 1):
                print(f"      {i}. \"{bigram}\" ({freq}x)")
        
        if results['failed']:
            print(f"\n❌ ÉCHECS D'EXTRACTION:")
            for fail in results['failed']:
                print(f"   - {self._extract_domain(fail['url'])}: {fail['reason'][:50]}...")
    
    async def test_all_queries(self):
        """Test sur les 3 requêtes avec URLs manuelles"""
        
        # URLs réelles approximatives du TOP 5 (basées sur une recherche manuelle)
        query_urls = {
            "nettoyage après inondation": [
                "https://www.service-public.fr/particuliers/vosdroits/F3050",
                "https://www.economie.gouv.fr/dgccrf/Publications/Vie-pratique/Fiches-pratiques/Degats-eaux-inondations",
                "https://www.lci.fr/societe/inondations-comment-nettoyer-sa-maison-apres-une-inondation-2131847.html",
                "https://www.maif.fr/conseils-prevention/la-maison/degats-des-eaux-inondations.html",
                "https://www.generali.fr/assurance-habitation/degats-des-eaux/nettoyage-maison-inondee/"
            ],
            "etat surface acier": [
                "https://fr.wikipedia.org/wiki/État_de_surface",
                "https://www.technologuepro.com/cours-genie-mecanique/cours-cotation-tolerancement/etats-surfaces.html",
                "https://www.mitutoyo.fr/webfoo/wp-content/uploads/Etat_de_surface.pdf",
                "https://www.directindustry.fr/fabricant-industriel/etat-surface-88991.html",
                "https://www.sandvik.coromant.com/fr-fr/knowledge/general-turning/roughness-and-surface-finish"
            ],
            "aide implantation": [
                "https://www.service-public.fr/professionnels/vosdroits/F22316",
                "https://www.economie.gouv.fr/cedef/creation-entreprise-aides-financieres",
                "https://www.bpifrance.fr/nos-solutions/financer-mon-projet-de-creation-reprise",
                "https://www.pole-emploi.fr/candidat/creation-entreprise/les-aides.html",
                "https://www.urssaf.fr/accueil/aides-et-mesures-covid-19/toutes-les-mesures-daide/exonerations.html"
            ]
        }
        
        print("🚀 TEST MANUEL SUR REQUÊTES GOOGLE RÉELLES")
        print("=" * 80)
        print("📍 Mode simulation avec URLs représentatives du TOP 5")
        
        all_results = []
        
        for i, (query, urls) in enumerate(query_urls.items(), 1):
            print(f"\n\n🎯 REQUÊTE {i}/{len(query_urls)}")
            result = await self.test_query_manual(query, urls)
            
            if result:
                all_results.append(result)
            
            if i < len(query_urls):
                print(f"\n⏳ Pause de 3 secondes avant requête suivante...")
                await asyncio.sleep(3)
        
        # Comparaison finale
        if len(all_results) > 1:
            self._compare_all_queries(all_results)
        
        return all_results
    
    def _compare_all_queries(self, all_results):
        """Comparaison entre toutes les requêtes"""
        
        print(f"\n{'='*80}")
        print(f"🆚 COMPARAISON GLOBALE DES 3 REQUÊTES")
        print(f"{'='*80}")
        
        print(f"{'Requête':<30} {'Succès':<8} {'Mots':<8} {'Moy/site':<8}")
        print("-" * 60)
        
        for result in all_results:
            query = result['query'][:28]
            successful = len(result['extractions'])
            total_words = sum([ext['word_count'] for ext in result['extractions']])
            avg_words = total_words // max(successful, 1)
            
            print(f"{query:<30} {successful}/5{'':<3} {total_words:<8,} {avg_words:<8,}")
        
        print(f"\n💡 INSIGHTS COMPARATIFS:")
        
        # Requête avec le plus de contenu
        max_words = max(all_results, key=lambda r: sum([ext['word_count'] for ext in r['extractions']]))
        max_total = sum([ext['word_count'] for ext in max_words['extractions']])
        print(f"   📈 Plus de contenu: '{max_words['query']}' ({max_total:,} mots)")
        
        # Meilleur taux de succès
        best_success = max(all_results, key=lambda r: len(r['extractions']))
        success_rate = len(best_success['extractions'])
        print(f"   🎯 Meilleur succès: '{best_success['query']}' ({success_rate}/5 sites)")
        
        # Analyse des domaines les plus représentés
        all_domains = []
        for result in all_results:
            for ext in result['extractions']:
                all_domains.append(ext['domain'])
        
        domain_freq = Counter(all_domains)
        if domain_freq:
            print(f"   🏆 Domaines les plus analysés:")
            for domain, freq in domain_freq.most_common(3):
                print(f"      - {domain}: {freq} fois")

async def main():
    tester = ManualSerpTester()
    await tester.test_all_queries()

if __name__ == "__main__":
    asyncio.run(main())