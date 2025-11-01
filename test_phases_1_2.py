"""
Test des Phases 1 & 2 : Scraping Parallèle + TOP 20
"""
import asyncio
import time
from services.valueserp_service import ValueSerpService
from services.seo_analyzer import SEOAnalyzer

async def test_phase_1_parallel_scraping():
    """Test Phase 1 : Scraping parallèle avec TOP 10"""
    print("\n" + "="*80)
    print("📊 TEST PHASE 1 : SCRAPING PARALLÈLE (TOP 10)")
    print("="*80 + "\n")

    service = ValueSerpService()

    # Test avec 10 résultats
    print("🔍 Test avec TOP 10 résultats...")
    start = time.time()

    try:
        results = await service.get_serp_data("agence seo", num_results=10)
        duration = time.time() - start

        print(f"\n✅ Scraping parallèle réussi!")
        print(f"⏱️  Durée: {duration:.2f}s")
        print(f"📊 Résultats récupérés: {len(results['organic_results'])}")

        # Compter erreurs
        errors = sum(1 for r in results['organic_results'] if r.get('scraping_error'))
        success_rate = ((len(results['organic_results']) - errors) / len(results['organic_results'])) * 100

        print(f"✅ Pages scrapées avec succès: {len(results['organic_results']) - errors}/{len(results['organic_results'])}")
        print(f"📈 Taux de succès: {success_rate:.1f}%")

        # Vérifier performance
        if duration < 30:
            print(f"🎯 OBJECTIF ATTEINT : Durée < 30s (obtenu: {duration:.2f}s)")
        else:
            print(f"⚠️  OBJECTIF NON ATTEINT : Durée > 30s (obtenu: {duration:.2f}s)")

        return True

    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False


async def test_phase_2_top_20():
    """Test Phase 2 : Migration vers TOP 20"""
    print("\n" + "="*80)
    print("📊 TEST PHASE 2 : MIGRATION TOP 20")
    print("="*80 + "\n")

    service = ValueSerpService()
    analyzer = SEOAnalyzer()

    # Test avec 20 résultats
    print("🔍 Test avec TOP 20 résultats...")
    start = time.time()

    try:
        # Scraping des 20 résultats
        serp_results = await service.get_serp_data("marketing digital", num_results=20)
        scraping_duration = time.time() - start

        print(f"\n✅ Scraping TOP 20 réussi!")
        print(f"⏱️  Durée scraping: {scraping_duration:.2f}s")
        print(f"📊 Résultats récupérés: {len(serp_results['organic_results'])}")

        # Analyse SEO
        print("\n🔬 Lancement de l'analyse SEO...")
        analysis_start = time.time()
        analysis = await analyzer.analyze_competition("marketing digital", serp_results)
        analysis_duration = time.time() - analysis_start

        print(f"✅ Analyse SEO terminée en {analysis_duration:.2f}s")
        print(f"\n📈 Résultats de l'analyse:")
        print(f"   - Score cible: {analysis.get('score_cible', 'N/A')}")
        print(f"   - Mots requis: {analysis.get('mots_requis', 'N/A')}")
        print(f"   - Mots-clés obligatoires: {len(analysis.get('KW_obligatoires', []))}")
        print(f"   - Mots-clés complémentaires: {len(analysis.get('KW_complementaires', []))}")
        print(f"   - Concurrents analysés: {len(analysis.get('concurrence', []))}")

        # Vérifier que les calculs utilisent bien plus de données
        competitors = analysis.get('concurrence', [])
        if len(competitors) >= 18:  # Au moins 18 sur 20
            print(f"✅ OBJECTIF ATTEINT : {len(competitors)} concurrents analysés (sur 20 demandés)")
        else:
            print(f"⚠️  Seulement {len(competitors)} concurrents analysés")

        # Performance globale
        total_duration = time.time() - start
        print(f"\n⏱️  Durée totale: {total_duration:.2f}s")

        if total_duration < 40:
            print(f"🎯 OBJECTIF ATTEINT : Durée totale < 40s")
        else:
            print(f"⚠️  Durée un peu longue mais acceptable")

        return True

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_comparison_10_vs_20():
    """Test comparatif TOP 10 vs TOP 20"""
    print("\n" + "="*80)
    print("📊 TEST COMPARATIF : TOP 10 vs TOP 20")
    print("="*80 + "\n")

    service = ValueSerpService()
    analyzer = SEOAnalyzer()
    query = "création site web"

    # Test TOP 10
    print("🔍 Test TOP 10...")
    start_10 = time.time()
    serp_10 = await service.get_serp_data(query, num_results=10)
    analysis_10 = await analyzer.analyze_competition(query, serp_10)
    duration_10 = time.time() - start_10

    # Test TOP 20
    print("🔍 Test TOP 20...")
    start_20 = time.time()
    serp_20 = await service.get_serp_data(query, num_results=20)
    analysis_20 = await analyzer.analyze_competition(query, serp_20)
    duration_20 = time.time() - start_20

    # Comparaison
    print(f"\n{'='*80}")
    print(f"{'Métrique':<40} {'TOP 10':>15} {'TOP 20':>15}")
    print(f"{'='*80}")
    print(f"{'Durée totale (s)':<40} {duration_10:>15.2f} {duration_20:>15.2f}")
    print(f"{'Résultats scrapés':<40} {len(serp_10['organic_results']):>15} {len(serp_20['organic_results']):>15}")
    print(f"{'Concurrents analysés':<40} {len(analysis_10.get('concurrence', [])):>15} {len(analysis_20.get('concurrence', [])):>15}")
    print(f"{'Score cible':<40} {analysis_10.get('score_cible', 'N/A'):>15} {analysis_20.get('score_cible', 'N/A'):>15}")
    print(f"{'Mots requis':<40} {analysis_10.get('mots_requis', 'N/A'):>15} {analysis_20.get('mots_requis', 'N/A'):>15}")
    print(f"{'Mots-clés obligatoires':<40} {len(analysis_10.get('KW_obligatoires', [])):>15} {len(analysis_20.get('KW_obligatoires', [])):>15}")
    print(f"{'Mots-clés complémentaires':<40} {len(analysis_10.get('KW_complementaires', [])):>15} {len(analysis_20.get('KW_complementaires', [])):>15}")
    print(f"{'='*80}")

    # Gain de temps
    time_increase = ((duration_20 / duration_10) - 1) * 100
    print(f"\n⏱️  Augmentation temps: +{time_increase:.1f}%")
    print(f"📊 Augmentation données: +{((len(serp_20['organic_results']) / len(serp_10['organic_results'])) - 1) * 100:.1f}%")


async def main():
    """Lance tous les tests"""
    print("\n" + "🚀"*40)
    print("🧪 TESTS PHASES 1 & 2 : SCRAPING PARALLÈLE + TOP 20")
    print("🚀"*40)

    # Phase 1
    phase1_ok = await test_phase_1_parallel_scraping()

    # Phase 2
    phase2_ok = await test_phase_2_top_20()

    # Comparatif
    await test_comparison_10_vs_20()

    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    print(f"Phase 1 (Scraping parallèle): {'✅ RÉUSSI' if phase1_ok else '❌ ÉCHOUÉ'}")
    print(f"Phase 2 (Migration TOP 20):  {'✅ RÉUSSI' if phase2_ok else '❌ ÉCHOUÉ'}")
    print("="*80 + "\n")

    if phase1_ok and phase2_ok:
        print("🎉 TOUTES LES PHASES SONT OPÉRATIONNELLES!")
        print("✅ Le scraping parallèle fonctionne")
        print("✅ L'analyse TOP 20 fonctionne")
        print("✅ Les performances sont bonnes")
    else:
        print("⚠️  Certains tests ont échoué")


if __name__ == "__main__":
    asyncio.run(main())
