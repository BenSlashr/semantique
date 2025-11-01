#!/usr/bin/env python3
"""
Test direct sur agence-slashr.fr pour debug
"""

import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_agence_slashr_direct():
    """Test direct avec debugging"""
    
    url = "https://agence-slashr.fr/"
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            html_content = response.text
        
        print(f"✅ HTML récupéré: {len(html_content)} caractères")
        
        # Debug BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\n🔍 ÉLÉMENTS TROUVÉS:")
        
        # Test sélecteurs un par un
        selectors = [
            'main',
            'article', 
            '[role="main"]',
            '.main-content',
            '.content',
            '.entry-content',
            '#content',
            'body'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for i, elem in enumerate(elements):
                    content = elem.get_text(separator=' ', strip=True)
                    word_count = len(content.split())
                    print(f"   {selector} [{i}]: {word_count} mots")
                    if word_count > 0:
                        preview = content[:200].replace('\n', ' ')
                        print(f"      Aperçu: {preview}...")
            else:
                print(f"   {selector}: AUCUN ÉLÉMENT")
        
        # Test body direct
        body = soup.find('body')
        if body:
            body_content = body.get_text(separator=' ', strip=True)
            print(f"\n📄 BODY DIRECT: {len(body_content.split())} mots")
            print(f"   Aperçu: {body_content[:300]}...")
        
        # Test sans suppression d'éléments
        print(f"\n🧹 TEST SANS NETTOYAGE:")
        raw_body = soup.find('body')
        if raw_body:
            raw_content = raw_body.get_text(separator=' ', strip=True)
            print(f"   Body brut: {len(raw_content.split())} mots")
        
        # Test avec suppression minimale
        soup_clean = BeautifulSoup(html_content, 'html.parser')
        for element in soup_clean(['script', 'style']):
            element.decompose()
        
        clean_body = soup_clean.find('body')
        if clean_body:
            clean_content = clean_body.get_text(separator=' ', strip=True)
            print(f"   Body nettoyé (script/style): {len(clean_content.split())} mots")
            print(f"   Aperçu nettoyé: {clean_content[:300]}...")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_agence_slashr_direct())