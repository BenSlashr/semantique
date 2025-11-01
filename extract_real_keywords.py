#!/usr/bin/env python3
"""
Extraction réelle des mots-clés via ValueSERP et SEOAnalyzer
"""

import asyncio
from services.valueserp_service import ValueSerpService
from services.seo_analyzer import SEOAnalyzer
import os
import time

class RealKeywordExtractor:
    def __init__(self):
        self.valueserp_service = ValueSerpService()
        self.seo_analyzer = SEOAnalyzer()
    
    def check_api_key(self):
        """Vérifie la présence de la clé API"""
        api_key = os.getenv("VALUESERP_API_KEY") or os.getenv("SERP_API_KEY")
        
        if not api_key:
            print("❌ ERREUR: Clé API ValueSERP introuvable")
            print("🔍 Variables d'environnement vérifiées:")
            print("   - VALUESERP_API_KEY")
            print("   - SERP_API_KEY") 
            print("\n💡 Veuillez fournir votre clé API ValueSERP")
            return None
        
        print(f"✅ Clé API trouvée: {api_key[:10]}...{api_key[-4:]}")
        return api_key
    
    async def extract_keywords_for_query(self, query: str) -> dict:
        """Extraction complète des mots-clés pour une requête"""
        
        print(f"\n{'='*80}")
        print(f"🎯 EXTRACTION RÉELLE: '{query}'")
        print(f"{'='*80}")
        
        try:
            start_time = time.time()
            
            # ÉTAPE 1: Récupération SERP via ValueSERP
            print(f"\n📡 ÉTAPE 1: Récupération SERP...")
            serp_results = await self.valueserp_service.get_serp_data(query, "France", "fr")
            
            if not serp_results or not serp_results.get('organic_results'):
                print(f"❌ Aucun résultat SERP pour '{query}'")
                return {'query': query, 'status': 'no_serp', 'error': 'Aucun résultat SERP'}
            
            organic_results = serp_results.get('organic_results', [])
            paa_questions = serp_results.get('paa', [])
            related_searches = serp_results.get('related_searches', [])
            
            print(f"✅ SERP récupérés:")
            print(f"   📝 Résultats organiques: {len(organic_results)}")
            print(f"   ❓ Questions PAA: {len(paa_questions)}")
            print(f"   🔗 Recherches associées: {len(related_searches)}")
            
            # ÉTAPE 2: Analyse sémantique avec SEOAnalyzer
            print(f"\n🧠 ÉTAPE 2: Analyse sémantique SEOAnalyzer...")
            
            analysis_results = await self.seo_analyzer.analyze_competition(query, serp_results)
            
            analysis_time = time.time() - start_time
            print(f"✅ Analyse terminée en {analysis_time:.2f}s")
            
            # ÉTAPE 3: Structuration des résultats
            return {
                'query': query,
                'status': 'success',
                'analysis_time': round(analysis_time, 2),
                'serp_data': {
                    'organic_count': len(organic_results),
                    'paa_questions': paa_questions,
                    'related_searches': related_searches,
                    'top_competitors': [
                        {
                            'position': r.get('position'),
                            'domain': r.get('domain', ''),
                            'title': r.get('title', ''),
                            'url': r.get('url', '')
                        }
                        for r in organic_results[:5]
                    ]
                },
                'seo_analysis': {
                    'target_seo_score': analysis_results.get('score_cible', 0),
                    'recommended_words': analysis_results.get('mots_requis', 0),
                    'max_overoptimization': analysis_results.get('max_suroptimisation', 0),
                    'required_keywords': [
                        {
                            'keyword': kw[0],
                            'frequency': kw[1],
                            'importance': kw[2],
                            'min_freq': kw[3],
                            'max_freq': kw[4]
                        }
                        for kw in analysis_results.get('KW_obligatoires', [])[:15]
                    ],
                    'complementary_keywords': [
                        {
                            'keyword': kw[0], 
                            'frequency': kw[1],
                            'importance': kw[2],
                            'min_freq': kw[3],
                            'max_freq': kw[4]
                        }
                        for kw in analysis_results.get('KW_complementaires', [])[:15]
                    ],
                    'ngrams': [
                        {
                            'ngram': ng[0],
                            'frequency': ng[1],
                            'importance': ng[2]
                        }
                        for ng in analysis_results.get('ngrams', [])[:10]
                    ],
                    'market_analysis': analysis_results.get('types_contenu', {}),
                    'generated_questions': analysis_results.get('questions', '')
                }
            }
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction: {e}")
            return {
                'query': query,
                'status': 'error', 
                'error': str(e)
            }
    
    def display_keyword_results(self, results: dict):
        """Affiche les résultats de manière structurée"""
        
        if results['status'] != 'success':
            print(f"❌ Échec pour '{results['query']}': {results.get('error', 'Erreur inconnue')}")
            return
        
        query = results['query']
        serp = results['serp_data']
        seo = results['seo_analysis']
        
        print(f"\n📊 RÉSULTATS POUR '{query.upper()}'")
        print("=" * 80)
        
        # Informations générales
        print(f"⏱️  Temps d'analyse: {results['analysis_time']}s")
        print(f"📝 Concurrents analysés: {serp['organic_count']}")
        print(f"🎯 Score SEO cible: {seo['target_seo_score']}")
        print(f"📊 Mots recommandés: {seo['recommended_words']}")
        print(f"⚠️  Max suroptimisation: {seo['max_overoptimization']}%")
        
        # TOP 5 Concurrents
        print(f"\n🏆 TOP 5 CONCURRENTS:")
        for comp in serp['top_competitors']:
            if comp['domain']:
                print(f"   #{comp['position']} {comp['domain']:<25} {comp['title'][:50]}...")
        
        # MOTS-CLÉS OBLIGATOIRES (Primaires)
        print(f"\n🎯 MOTS-CLÉS PRIMAIRES (OBLIGATOIRES):")
        if seo['required_keywords']:
            for i, kw in enumerate(seo['required_keywords'], 1):
                importance = "🔥 CRITIQUE" if kw['importance'] >= 80 else "⭐ IMPORTANT" if kw['importance'] >= 60 else "📌 STANDARD"
                print(f"   {i:2}. {kw['keyword']:<25} {kw['frequency']:>3}x {importance} (min:{kw['min_freq']}, max:{kw['max_freq']})")
        else:
            print("   ❌ Aucun mot-clé obligatoire identifié")
        
        # MOTS-CLÉS COMPLÉMENTAIRES (Secondaires)
        print(f"\n💎 MOTS-CLÉS SECONDAIRES (COMPLÉMENTAIRES):")
        if seo['complementary_keywords']:
            for i, kw in enumerate(seo['complementary_keywords'], 1):
                importance = "🔥 CRITIQUE" if kw['importance'] >= 80 else "⭐ IMPORTANT" if kw['importance'] >= 60 else "📌 STANDARD"
                print(f"   {i:2}. {kw['keyword']:<25} {kw['frequency']:>3}x {importance} (min:{kw['min_freq']}, max:{kw['max_freq']})")
        else:
            print("   ❌ Aucun mot-clé complémentaire identifié")
        
        # EXPRESSIONS N-GRAMMES
        print(f"\n🔗 EXPRESSIONS CLÉS (N-GRAMMES):")
        if seo['ngrams']:
            for i, ng in enumerate(seo['ngrams'], 1):
                importance = "🔥 CRITIQUE" if ng['importance'] >= 80 else "⭐ IMPORTANT" if ng['importance'] >= 60 else "📌 STANDARD"
                print(f"   {i:2}. \"{ng['ngram']}\" {ng['frequency']:>3}x {importance}")
        else:
            print("   ❌ Aucune expression identifiée")
        
        # QUESTIONS PAA
        print(f"\n❓ QUESTIONS PEOPLE ALSO ASK:")
        if serp['paa_questions']:
            for i, question in enumerate(serp['paa_questions'][:5], 1):
                print(f"   {i}. {question}")
        else:
            print("   ❌ Aucune question PAA")
        
        # RECHERCHES ASSOCIÉES
        print(f"\n🔍 RECHERCHES ASSOCIÉES:")
        if serp['related_searches']:
            for i, search in enumerate(serp['related_searches'][:8], 1):
                print(f"   {i}. {search}")
        else:
            print("   ❌ Aucune recherche associée")
        
        # ANALYSE MARCHÉ
        print(f"\n📈 ANALYSE MARCHÉ:")
        market = seo['market_analysis']
        if market:
            for content_type, stats in market.items():
                if isinstance(stats, dict) and 'count' in stats:
                    print(f"   📄 {content_type}: {stats['count']} sites ({stats.get('percentage', 0):.1f}%)")
        
        # QUESTIONS GÉNÉRÉES
        if seo['generated_questions']:
            print(f"\n💡 QUESTIONS GÉNÉRÉES PAR IA:")
            questions = seo['generated_questions'].split('\n')
            for i, q in enumerate(questions[:5], 1):
                if q.strip():
                    print(f"   {i}. {q.strip()}")
    
    async def extract_all_queries(self):
        """Extraction pour les 3 requêtes demandées"""
        
        queries = [
            "nettoyage après inondation",
            "etat surface acier", 
            "aide implantation"
        ]
        
        print("🚀 EXTRACTION RÉELLE DES MOTS-CLÉS AVEC VALUESERP")
        print("=" * 80)
        
        # Vérification API
        api_key = self.check_api_key()
        if not api_key:
            user_key = input("\n🔑 Veuillez entrer votre clé API ValueSERP: ").strip()
            if user_key:
                os.environ['VALUESERP_API_KEY'] = user_key
                self.valueserp_service.api_key = user_key
                print(f"✅ Clé API configurée: {user_key[:10]}...{user_key[-4:]}")
            else:
                print("❌ Aucune clé API fournie, abandon.")
                return []
        
        all_results = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n\n🎯 REQUÊTE {i}/{len(queries)}")
            
            result = await self.extract_keywords_for_query(query)
            all_results.append(result)
            
            self.display_keyword_results(result)
            
            # Pause entre requêtes
            if i < len(queries):
                print(f"\n⏳ Pause de 3 secondes avant requête suivante...")
                await asyncio.sleep(3)
        
        # Résumé final
        self.display_final_summary(all_results)
        
        return all_results
    
    def display_final_summary(self, all_results: list):
        """Affiche un résumé comparatif final"""
        
        print(f"\n{'='*80}")
        print("📊 RÉSUMÉ COMPARATIF DES 3 REQUÊTES")
        print("=" * 80)
        
        successful_results = [r for r in all_results if r['status'] == 'success']
        
        if not successful_results:
            print("❌ Aucune requête n'a abouti")
            return
        
        print(f"{'Requête':<30} {'Primaires':<10} {'Secondaires':<12} {'Expressions':<12} {'Score':<6}")
        print("-" * 80)
        
        for result in successful_results:
            query = result['query'][:28]
            seo = result['seo_analysis']
            
            primary_count = len(seo['required_keywords'])
            secondary_count = len(seo['complementary_keywords'])  
            expressions_count = len(seo['ngrams'])
            score = seo['target_seo_score']
            
            print(f"{query:<30} {primary_count:<10} {secondary_count:<12} {expressions_count:<12} {score:<6}")
        
        # Insights
        print(f"\n💡 INSIGHTS GLOBAUX:")
        
        # Requête la plus riche en mots-clés
        richest = max(successful_results, key=lambda r: len(r['seo_analysis']['required_keywords']) + len(r['seo_analysis']['complementary_keywords']))
        total_kw = len(richest['seo_analysis']['required_keywords']) + len(richest['seo_analysis']['complementary_keywords'])
        print(f"   🏆 Plus riche en mots-clés: '{richest['query']}' ({total_kw} mots-clés)")
        
        # Score SEO le plus élevé
        highest_score = max(successful_results, key=lambda r: r['seo_analysis']['target_seo_score'])
        print(f"   📈 Score SEO le plus élevé: '{highest_score['query']}' ({highest_score['seo_analysis']['target_seo_score']} points)")
        
        # Plus d'expressions
        most_expressions = max(successful_results, key=lambda r: len(r['seo_analysis']['ngrams']))
        print(f"   🔗 Plus d'expressions: '{most_expressions['query']}' ({len(most_expressions['seo_analysis']['ngrams'])} expressions)")

async def main():
    extractor = RealKeywordExtractor()
    await extractor.extract_all_queries()

if __name__ == "__main__":
    asyncio.run(main())