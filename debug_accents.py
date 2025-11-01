#!/usr/bin/env python3
"""
Debug pour la détection des accents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.seo_analyzer import SEOAnalyzer

def debug_accent_detection():
    analyzer = SEOAnalyzer()
    
    # Test avec accents
    content = "La créatinë monohydraté améliore. Créatine monohydrate recommandé."
    keyword = "créatine monohydrate"
    
    print(f"🔍 DEBUG DÉTECTION ACCENTS")
    print(f"Contenu: {content}")
    print(f"Mot-clé: {keyword}")
    print()
    
    # Étape 1: Normalisation
    normalized_content = analyzer._normalize_for_detection(content)
    normalized_keyword = analyzer._normalize_for_detection(keyword)
    
    print(f"Contenu normalisé: {normalized_content}")
    print(f"Mot-clé normalisé: {normalized_keyword}")
    print()
    
    # Étape 2: Tokenisation
    words = normalized_content.split()
    kw_parts = normalized_keyword.split()
    
    print(f"Mots: {words}")
    print(f"Parties mot-clé: {kw_parts}")
    print()
    
    # Étape 3: Fenêtre glissante
    candidates_count = 0
    k = len(kw_parts)
    
    print(f"Recherche de '{' '.join(kw_parts)}' dans le texte:")
    for i in range(len(words) - k + 1):
        window = words[i:i+k]
        match = all(words[i + j] == kw_parts[j] for j in range(k))
        print(f"  Position {i}: {window} → {'✅ MATCH' if match else '❌'}")
        if match:
            candidates_count += 1
    
    print(f"\nRésultat final: {candidates_count} occurrences")
    
    # Test avec la méthode complète
    result = analyzer._detect_keyword_hybrid(content, keyword)
    print(f"Méthode complète: {result} occurrences")
    
    # Debug validation contextuelle
    print(f"\n🔍 DEBUG VALIDATION CONTEXTUELLE:")
    risky = ("'" in keyword) or ("-" in keyword) or (len(kw_parts) > 1)
    print(f"Cas complexe détecté: {risky}")
    
    if risky:
        valid_count_original = analyzer._validate_with_regex(content, keyword)
        valid_count_normalized = analyzer._validate_with_regex(normalized_content, normalized_keyword)
        print(f"Validation regex (original): {valid_count_original} occurrences")
        print(f"Validation regex (normalisé): {valid_count_normalized} occurrences")
        print(f"Fenêtre glissante: {candidates_count} occurrences")
        print(f"Résultat final: min({candidates_count}, {valid_count_normalized}) = {min(candidates_count, valid_count_normalized)}")

if __name__ == "__main__":
    debug_accent_detection()