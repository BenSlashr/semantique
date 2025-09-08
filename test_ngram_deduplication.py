#!/usr/bin/env python3
"""
Script de test pour la déduplication des n-grams (Phase 1)
"""

from services.seo_analyzer import SEOAnalyzer

def test_ngram_deduplication():
    """Test la déduplication des n-grams avec des exemples similaires à 'école de commerce'"""
    
    analyzer = SEOAnalyzer()
    
    # Simulation de n-grams similaires comme dans votre exemple
    test_ngrams = [
        ["l école de commerce", 6, 99],
        ["école de commerce après", 4, 91],
        ["grande école de commerce", 4, 91],
        ["école de commerce pour", 2, 83],
        ["école de commerce inscription", 2, 83],
        ["d école de commerce", 2, 83],
        ["son école de commerce", 2, 83],
        ["écoles de commerce sont", 3, 62],
        ["écoles de commerce post", 3, 62],
        ["paris école de gestion", 3, 62],
        ["écoles de commerce post bac", 3, 62],
        ["d écoles de commerce", 2, 58],
        ["écoles supérieures de commerce", 2, 58],
        ["grandes écoles de commerce", 2, 58],
        ["écoles de commerce proposent", 2, 58],
        ["sortie de l école", 2, 58],
        ["ecole de commerce bts", 2, 58],
        ["quelques exemples de professions", 2, 43],
        ["monde de l entreprise", 3, 37],
        ["grade de licence bac", 3, 37],
        ["grade de licence bac 3", 3, 37],
        ["commerce après le bac", 2, 33],
        ["différents moments de votre", 2, 33],
        ["d intégrer une école", 2, 33],
        ["fonction de votre profil", 2, 33],
    ]
    
    print("🧪 Test de déduplication des n-grams")
    print("=" * 60)
    print(f"📊 Données d'entrée: {len(test_ngrams)} n-grams")
    print()
    
    print("📋 N-GRAMS AVANT DÉDUPLICATION:")
    print("-" * 40)
    for i, (ngram, freq, score) in enumerate(test_ngrams[:10], 1):
        print(f"{i:2d}. {ngram:<35} (fréq: {freq}, score: {score})")
    print(f"    ... et {len(test_ngrams) - 10} autres")
    print()
    
    # Test de la déduplication
    deduplicated = analyzer._deduplicate_ngrams(test_ngrams)
    
    print("\n📋 N-GRAMS APRÈS DÉDUPLICATION:")
    print("-" * 40)
    for i, (ngram, freq, score) in enumerate(deduplicated, 1):
        print(f"{i:2d}. {ngram:<35} (fréq: {freq}, score: {score})")
    
    print(f"\n📈 RÉSULTATS:")
    print(f"   - Avant: {len(test_ngrams)} n-grams")
    print(f"   - Après: {len(deduplicated)} n-grams")
    print(f"   - Réduction: {len(test_ngrams) - len(deduplicated)} n-grams (-{((len(test_ngrams) - len(deduplicated)) / len(test_ngrams) * 100):.1f}%)")
    
    # Analyse des groupes créés
    print(f"\n🔍 ANALYSE DES AMÉLIORATIONS:")
    
    # Chercher les mots "école de commerce" dans les résultats
    commerce_related = [(ngram, freq, score) for ngram, freq, score in deduplicated if "école" in ngram or "commerce" in ngram]
    print(f"   - N-grams liés à 'école/commerce': {len(commerce_related)}")
    for ngram, freq, score in commerce_related:
        print(f"     → {ngram} (fréq: {freq})")
    
    # Vérifier la diversité thématique
    themes = {
        'formation': ['formation', 'cursus', 'diplôme', 'étude'],
        'débouchés': ['métier', 'profession', 'carrière', 'emploi'],
        'admission': ['inscription', 'intégrer', 'admission', 'concours'],
        'spécialisation': ['spécialisation', 'finance', 'marketing', 'management']
    }
    
    print(f"\n🎯 DIVERSITÉ THÉMATIQUE:")
    for theme, keywords in themes.items():
        theme_ngrams = [(ngram, freq, score) for ngram, freq, score in deduplicated 
                       if any(keyword in ngram.lower() for keyword in keywords)]
        if theme_ngrams:
            print(f"   - {theme.capitalize()}: {len(theme_ngrams)} n-grams")
            for ngram, freq, score in theme_ngrams[:3]:  # Top 3 par thème
                print(f"     → {ngram}")

if __name__ == "__main__":
    test_ngram_deduplication() 