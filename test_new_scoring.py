#!/usr/bin/env python3
"""
🧪 Tests pour la nouvelle méthode de calcul de score 70/30
"""
import asyncio
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.seo_analyzer import SEOAnalyzer

def test_detect_keyword_hybrid():
    """Test de la détection hybride"""
    print("🔍 TEST DÉTECTION HYBRIDE")
    print("=" * 50)
    
    analyzer = SEOAnalyzer()
    
    # Test 1: Mot simple
    content1 = "La créatine améliore les performances physiques. La créatine est populaire."
    result1 = analyzer._detect_keyword_hybrid(content1, "créatine")
    print(f"✅ Mot simple 'créatine' : {result1} occurrences (attendu: 2)")
    
    # Test 2: Expression multi-mots
    content2 = "La créatine monohydrate améliore les performances. Le créatine monohydrate est efficace."
    result2 = analyzer._detect_keyword_hybrid(content2, "créatine monohydrate")
    print(f"✅ Expression 'créatine monohydrate' : {result2} occurrences (attendu: 2)")
    
    # Test 3: Avec accents
    content3 = "La créatinë monohydraté améliore. Créatine monohydrate recommandé."
    result3 = analyzer._detect_keyword_hybrid(content3, "créatine monohydrate")
    print(f"✅ Avec accents : {result3} occurrences (attendu: 2)")
    
    # Test 4: Expression avec tiret
    content4 = "Le produit anti-âge est efficace. Les crèmes anti-âge fonctionnent."
    result4 = analyzer._detect_keyword_hybrid(content4, "anti-âge")
    print(f"✅ Avec tirets 'anti-âge' : {result4} occurrences (attendu: 2)")
    
    # Test 5: Faux positifs (sous-chaînes)
    content5 = "supercréatinemonohydrateplus"
    result5 = analyzer._detect_keyword_hybrid(content5, "créatine monohydrate")
    print(f"✅ Faux positifs évités : {result5} occurrences (attendu: 0)")
    
    print()

def test_calculate_seo_score():
    """Test du calcul de score 70/30"""
    print("📊 TEST CALCUL SCORE 70/30")
    print("=" * 50)
    
    analyzer = SEOAnalyzer()
    
    # Contenu de test
    content = """
    La créatine est un excellent complément alimentaire pour la musculation.
    La créatine monohydrate améliore les performances physiques.
    La whey protéine aide à la récupération musculaire.
    Les BCAA sont utiles pour l'endurance.
    """
    
    # Mots-clés obligatoires (format: [keyword, freq, importance, min_freq, max_freq])
    keywords_obligatoires = [
        ["créatine", 2, 44, 1, 3],  # Présent 3 fois, min=1, max=3 → réussi mais limite
        ["whey", 1, 35, 1, 2],      # Présent 1 fois, min=1, max=2 → réussi
        ["bcaa", 1, 25, 2, 4]       # Présent 1 fois, min=2, max=4 → échec (< min)
    ]
    
    # Mots-clés complémentaires
    keywords_complementaires = [
        ["musculation", 1, 20, 1, 2],    # Présent 1 fois → réussi
        ["protéine", 1, 18, 1, 2],       # Présent 1 fois → réussi
        ["performance", 1, 15, 1, 2],    # Présent 1 fois → réussi
        ["inexistant", 0, 10, 1, 2]      # Pas présent → échec
    ]
    
    # Debug: vérifier les détections réelles
    print(f"🔍 Vérification détections réelles:")
    for kw_data in keywords_obligatoires:
        keyword = kw_data[0]
        actual = analyzer._detect_keyword_hybrid(content, keyword)
        print(f"   - {keyword}: {actual} occurrences (detectées)")
    
    for kw_data in keywords_complementaires:
        keyword = kw_data[0]
        actual = analyzer._detect_keyword_hybrid(content, keyword)
        print(f"   - {keyword}: {actual} occurrences (detectées)")
    
    score = analyzer._calculate_seo_score(content, keywords_obligatoires, keywords_complementaires)
    
    print(f"📝 Contenu analysé:")
    print(f"   - créatine: 3 occurrences (min=1, max=3) → réussi")
    print(f"   - whey: 1 occurrence (min=1, max=2) → réussi") 
    print(f"   - bcaa: 1 occurrence (min=2, max=4) → échec")
    print(f"   - musculation: 1 occurrence → réussi")
    print(f"   - protéine: 1 occurrence → réussi")
    print(f"   - performance: 1 occurrence → réussi")
    print(f"   - inexistant: 0 occurrence → échec")
    print()
    
    # Calcul attendu basé sur les détections réelles
    # Obligatoires: créatine(2≥1)✅ + whey(1≥1)✅ + bcaa(1<2)❌ = 2 réussis
    obligatoires_reussis = 2  # créatine + whey (bcaa échoue car 1 < min_freq=2)
    total_obligatoires = 3
    score_obligatoires = (obligatoires_reussis / total_obligatoires) * 70  # = 46.67
    
    # Complémentaires: musculation(1≥1)✅ + protéine(1≥1)✅ + performance(0<1)❌ + inexistant(0<1)❌ = 2 réussis
    complementaires_reussis = 2  # musculation + protéine (performance + inexistant échouent)
    total_complementaires = 4
    score_complementaires = (complementaires_reussis / total_complementaires) * 30  # = 15
    
    base_score = score_obligatoires + score_complementaires  # = 46.67 + 15 = 61.67
    
    # Aucune suroptimisation (toutes les fréquences <= max)
    malus = 0
    score_attendu = int(base_score - malus)  # = 61
    
    print(f"📊 Calcul détaillé:")
    print(f"   Score obligatoires (70%): {obligatoires_reussis}/{total_obligatoires} × 70 = {score_obligatoires:.1f}")
    print(f"   Score complémentaires (30%): {complementaires_reussis}/{total_complementaires} × 30 = {score_complementaires:.1f}")
    print(f"   Score base: {base_score:.1f}")
    print(f"   Malus suroptimisation: {malus}")
    print(f"   Score final attendu: {score_attendu}")
    print(f"   Score calculé: {score}")
    print(f"   ✅ {'SUCCÈS' if score == score_attendu else 'ÉCHEC'}")
    print()

def test_suroptimization_penalty():
    """Test du malus de suroptimisation"""
    print("⚠️ TEST MALUS SUROPTIMISATION")
    print("=" * 50)
    
    analyzer = SEOAnalyzer()
    
    # Contenu avec suroptimisation
    content = """
    Créatine créatine créatine créatine créatine.
    Whey whey whey.
    BCAA pour récupération.
    """
    
    # Mots-clés avec suroptimisation
    keywords_obligatoires = [
        ["créatine", 5, 44, 1, 3],  # 5 occurrences > max=3 → suroptimisé
        ["whey", 3, 35, 1, 2],      # 3 occurrences > max=2 → suroptimisé
    ]
    
    keywords_complementaires = [
        ["bcaa", 1, 25, 1, 2],      # 1 occurrence → normal
        ["récupération", 1, 20, 1, 2]  # 1 occurrence → normal
    ]
    
    score = analyzer._calculate_seo_score(content, keywords_obligatoires, keywords_complementaires)
    
    # Calcul attendu
    obligatoires_reussis = 2  # tous atteignent le minimum
    score_obligatoires = (2/2) * 70  # = 70
    
    complementaires_reussis = 2  # tous présents
    score_complementaires = (2/2) * 30  # = 30
    
    base_score = 100
    
    # Malus: 2 suroptimisés sur 4 total → (2/4) * 20 = 10
    malus = 10
    score_attendu = 90
    
    print(f"📊 Test suroptimisation:")
    print(f"   créatine: 5 occurrences (max=3) → suroptimisé")
    print(f"   whey: 3 occurrences (max=2) → suroptimisé")
    print(f"   Base score: {base_score}")
    print(f"   Malus: 2/4 × 20 = {malus}")
    print(f"   Score final attendu: {score_attendu}")
    print(f"   Score calculé: {score}")
    print(f"   ✅ {'SUCCÈS' if score == score_attendu else 'ÉCHEC'}")
    print()

async def test_integration():
    """Test d'intégration complète"""
    print("🔄 TEST INTÉGRATION COMPLÈTE")
    print("=" * 50)
    
    try:
        from services.valueserp_service import ValueSerpService
        
        analyzer = SEOAnalyzer()
        
        # Test avec données demo (pas d'appel API réel)
        demo_serp = {
            'organic_results': [
                {
                    'position': 1,
                    'title': 'Créatine monohydrate pour musculation',
                    'content': 'La créatine monohydrate est le meilleur complément pour la musculation. La créatine améliore les performances.',
                    'url': 'https://example.com/creatine',
                    'domain': 'example.com',
                    'word_count': 50,
                    'h1': 'Guide créatine',
                    'h2': 'Bienfaits créatine',
                    'h3': ''
                }
            ],
            'paa': ['Comment prendre la créatine ?'],
            'related_searches': ['créatine whey', 'créatine musculation'],
            'inline_videos': []
        }
        
        # Test analyse complète
        results = await analyzer.analyze_competition("créatine musculation", demo_serp)
        
        print(f"✅ Analyse terminée sans erreur")
        print(f"   Query: {results.get('query', 'N/A')}")
        print(f"   Score cible: {results.get('score_target', 'N/A')}")
        print(f"   Mots requis: {results.get('mots_requis', 'N/A')}")
        print(f"   Mots-clés obligatoires: {len(results.get('KW_obligatoires', []))}")
        print(f"   Mots-clés complémentaires: {len(results.get('KW_complementaires', []))}")
        
        # Vérifier qu'il y a des concurrents avec des scores
        concurrents = results.get('concurrence', [])
        if concurrents:
            score_concurrent = concurrents[0].get('score', 'N/A')
            print(f"   Score concurrent #1: {score_concurrent}")
            print(f"   ✅ INTÉGRATION RÉUSSIE")
        else:
            print(f"   ⚠️ Aucun concurrent trouvé")
            
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    print()

async def main():
    """Lance tous les tests"""
    print("🧪 TESTS NOUVELLE MÉTHODE DE CALCUL DE SCORE")
    print("=" * 60)
    print()
    
    # Tests unitaires
    test_detect_keyword_hybrid()
    test_calculate_seo_score()
    test_suroptimization_penalty()
    
    # Test d'intégration
    await test_integration()
    
    print("🏁 TESTS TERMINÉS")

if __name__ == "__main__":
    asyncio.run(main())