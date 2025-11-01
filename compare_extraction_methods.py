#!/usr/bin/env python3
"""
Script pour comparer l'ancienne et la nouvelle méthode d'extraction de contenu
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from services.valueserp_service import ValueSerpService

def extract_content_old_method(html_content):
    """Ancienne méthode: contenu complet"""
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text()

def extract_content_new_method(html_content):
    """Nouvelle méthode: contenu principal seulement"""
    soup = BeautifulSoup(html_content, 'html.parser')
    service = ValueSerpService()
    return service._extract_content(soup)

async def compare_extraction_methods():
    """Compare les deux méthodes d'extraction"""
    
    # URL de test
    test_url = "https://fr.wikipedia.org/wiki/Cr%C3%A9atine"
    
    print("🔬 Comparaison des méthodes d'extraction de contenu")
    print("=" * 60)
    print(f"🌐 URL de test: {test_url}")
    print()
    
    try:
        # Récupération de la page
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(test_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                print(f"❌ Erreur HTTP {response.status_code}")
                return
            
            html_content = response.text
            
            # Test ancienne méthode
            print("📊 ANCIENNE MÉTHODE (contenu complet)")
            print("-" * 40)
            old_content = extract_content_old_method(html_content)
            old_words = len(old_content.split())
            print(f"   - Nombre de mots: {old_words}")
            print(f"   - Longueur en caractères: {len(old_content)}")
            print(f"   - Début du contenu: {old_content[:200]}...")
            print()
            
            # Test nouvelle méthode
            print("📊 NOUVELLE MÉTHODE (contenu principal)")
            print("-" * 40)
            
            new_content = extract_content_new_method(html_content)
            new_words = len(new_content.split())
            print(f"   - Nombre de mots: {new_words}")
            print(f"   - Longueur en caractères: {len(new_content)}")
            print(f"   - Début du contenu: {new_content[:200]}...")
            print()
            
            # Comparaison
            print("📈 COMPARAISON")
            print("-" * 40)
            word_reduction = ((old_words - new_words) / old_words) * 100 if old_words > 0 else 0
            char_reduction = ((len(old_content) - len(new_content)) / len(old_content)) * 100 if len(old_content) > 0 else 0
            
            print(f"   - Réduction en mots: {word_reduction:.1f}% ({old_words} → {new_words})")
            print(f"   - Réduction en caractères: {char_reduction:.1f}%")
            print(f"   - Rapport de compression: {new_words/old_words:.2f}x" if old_words > 0 else "   - Rapport: N/A")
            
            # Analyse qualitative
            print()
            print("🎯 ANALYSE QUALITATIVE")
            print("-" * 40)
            
            # Mots typiques de navigation à chercher
            nav_words = ['menu', 'navigation', 'accueil', 'contact', 'mentions', 'newsletter', 'suivez-nous', 'réseaux sociaux']
            
            old_nav_count = sum(old_content.lower().count(word) for word in nav_words)
            new_nav_count = sum(new_content.lower().count(word) for word in nav_words)
            
            print(f"   - Mots de navigation (ancienne): {old_nav_count}")
            print(f"   - Mots de navigation (nouvelle): {new_nav_count}")
            print(f"   - Réduction du bruit: {((old_nav_count - new_nav_count) / old_nav_count * 100):.1f}%" if old_nav_count > 0 else "   - Réduction du bruit: N/A")
            
            if word_reduction > 20:
                print("   ✅ Bonne réduction du contenu parasité")
            elif word_reduction > 10:
                print("   ⚠️ Réduction modérée")
            else:
                print("   ❌ Peu de réduction, vérifier la méthode")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(compare_extraction_methods()) 