#!/usr/bin/env python3
"""
Script de diagnostic pour l'extraction de contenu
"""

import asyncio
import httpx
from bs4 import BeautifulSoup

async def debug_extraction():
    """Débogue l'extraction de contenu étape par étape"""
    
    test_url = "https://fr.wikipedia.org/wiki/Cr%C3%A9atine"
    
    print("🔍 Diagnostic d'extraction de contenu")
    print("=" * 50)
    print(f"URL: {test_url}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(test_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                print(f"❌ Erreur HTTP {response.status_code}")
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Étape 1: Suppression des scripts et styles
            print("📋 ÉTAPE 1: Suppression des scripts et styles")
            scripts_before = len(soup.find_all(['script', 'style']))
            for script in soup(["script", "style"]):
                script.decompose()
            print(f"   - Scripts/styles supprimés: {scripts_before}")
            
            # Étape 2: Suppression des éléments de navigation
            print("\n📋 ÉTAPE 2: Suppression des éléments de navigation")
            nav_elements_before = len(soup.find_all(["nav", "header", "footer", "aside"]))
            for element in soup(["nav", "header", "footer", "aside", "noscript"]):
                element.decompose()
            print(f"   - Éléments de navigation supprimés: {nav_elements_before}")
            
            # Étape 3: Test des sélecteurs principaux
            print("\n📋 ÉTAPE 3: Test des sélecteurs principaux")
            main_selectors = [
                'main', 'article', '[role="main"]', '.main-content', '.content',
                '.mw-parser-output', '#bodyContent', '.entry-content'
            ]
            
            for selector in main_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(separator=' ', strip=True)
                    print(f"   ✅ {selector}: {len(text)} caractères")
                    if len(text) > 100:
                        print(f"      Début: {text[:100]}...")
                        return text
                else:
                    print(f"   ❌ {selector}: non trouvé")
            
            # Étape 4: Analyse des divs avec plus de contenu
            print("\n📋 ÉTAPE 4: Analyse des plus gros blocs")
            all_divs = soup.find_all('div')
            div_sizes = []
            
            for i, div in enumerate(all_divs[:10]):  # Premiers 10 divs
                text = div.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    div_classes = ' '.join(div.get('class', []))
                    div_id = div.get('id', '')
                    div_sizes.append((i, len(text), div_classes, div_id, text[:100]))
            
            div_sizes.sort(key=lambda x: x[1], reverse=True)
            
            print("   Top 5 des plus gros blocs:")
            for i, (idx, size, classes, div_id, preview) in enumerate(div_sizes[:5]):
                print(f"   {i+1}. Div #{idx}: {size} chars, classes='{classes}', id='{div_id}'")
                print(f"      Aperçu: {preview}...")
                print()
            
            # Étape 5: Contenu total restant
            print("📋 ÉTAPE 5: Contenu total après nettoyage")
            total_text = soup.get_text(separator=' ', strip=True)
            print(f"   - Contenu total: {len(total_text)} caractères")
            if len(total_text) > 100:
                print(f"   - Début: {total_text[:200]}...")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(debug_extraction()) 