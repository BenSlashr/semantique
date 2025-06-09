import asyncio
from services.seo_analyzer import SEOAnalyzer
from services.valueserp_service import ValueSerpService

async def test_filtering():
    """Test le filtrage des expressions de mots-clés"""
    valueserp = ValueSerpService()
    analyzer = SEOAnalyzer()
    
    print("🧪 Test du filtrage des expressions de mots-clés")
    print("=" * 60)
    
    # Test avec la requête agence seo lille
    print("\n🔍 Test avec 'agence seo lille'")
    serp_data = await valueserp.get_serp_data('agence seo lille')
    results = await analyzer.analyze_competition('agence seo lille', serp_data)
    
    print('\n✅ EXPRESSIONS 2 MOTS FILTRÉES (TOP 10):')
    for i, bigram in enumerate(results['bigrams'][:10]):
        print(f'{i+1:2d}. {bigram[0]:25} (fréq: {bigram[1]}, score: {bigram[2]})')
    
    print('\n✅ EXPRESSIONS 3 MOTS FILTRÉES (TOP 10):')
    for i, trigram in enumerate(results['trigrams'][:10]):
        print(f'{i+1:2d}. {trigram[0]:35} (fréq: {trigram[1]}, score: {trigram[2]})')
    
    # Test des fonctions de validation individuellement
    print('\n🧪 TEST DES FILTRES INDIVIDUELS:')
    
    # Test bigrams
    test_bigrams = [
        "agence seo",           # ✅ Valide
        "seo lille",            # ✅ Valide  
        "de votre",             # ❌ Mots vides
        "sur les",              # ❌ Mots vides
        "agence de",            # ❌ Finit par mot vide
        "le site",              # ❌ Commence par mot vide
        "référencement naturel", # ✅ Valide
        "à la",                 # ❌ Pattern invalide
        "web design"            # ✅ Valide
    ]
    
    print('\nTest filtrage bigrams:')
    for bigram in test_bigrams:
        is_valid = analyzer._is_valid_bigram(bigram)
        status = "✅" if is_valid else "❌"
        print(f'  {status} "{bigram}"')
    
    # Test trigrams
    test_trigrams = [
        "agence seo lille",          # ✅ Valide
        "audit seo gratuit",         # ✅ Valide
        "référencement naturel google", # ✅ Valide
        "de la part",                # ❌ Commence par mot vide
        "site web professionnel",    # ✅ Valide
        "agence de communication",   # ✅ Valide (mot vide au milieu autorisé)
        "nous sommes experts",       # ❌ Pattern invalide
        "formation seo avancée"      # ✅ Valide
    ]
    
    print('\nTest filtrage trigrams:')
    for trigram in test_trigrams:
        is_valid = analyzer._is_valid_trigram(trigram)
        status = "✅" if is_valid else "❌"
        print(f'  {status} "{trigram}"')

if __name__ == "__main__":
    asyncio.run(test_filtering()) 