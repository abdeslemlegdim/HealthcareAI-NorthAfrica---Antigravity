#!/usr/bin/env python
"""Test multilingual response purity after language consistency fixes."""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8001"

def test_multilingual():
    """Run multilingual tests to validate language purity."""
    
    # Test cases: (language, question)
    tests = [
        ("en", "What are symptoms of pneumonia?"),
        ("fr", "Quels sont les symptômes de la pneumonie?"),
        ("ar", "ما هي أعراض الالتهاب الرئوي؟"),
    ]
    
    print("\n" + "="*70)
    print("MULTILINGUAL RESPONSE PURITY TEST (Language Consistency Fixes)")
    print("="*70 + "\n")
    
    for lang, question in tests:
        print(f"\n{'-'*70}")
        print(f"Language: {lang.upper()} | Question: {question[:50]}")
        print('-'*70)
        
        try:
            # Call RAG query endpoint
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/query",
                json={
                    "question": question,
                    "language": lang,
                    "enrich_external_sources": False
                },
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                continue
            
            data = response.json()
            print(f"✅ Status 200 - Response received")
            print(f"  Title: {data.get('title', 'N/A')}")
            print(f"  Response Language: {data.get('language', 'unknown')}")
            print(f"  Confidence: {data.get('confidence', 0)*100:.1f}%")
            
            # Validate symptom purity
            symptoms = data.get('symptoms', [])
            causes = data.get('causes', [])
            
            if symptoms:
                print(f"\n  Symptoms ({len(symptoms)} items):")
                for s in symptoms[:2]:
                    clean_s = s[:70] + "..." if len(s) > 70 else s
                    print(f"    • {clean_s}")
            
            if causes:
                print(f"\n  Causes ({len(causes)} items):")
                for c in causes[:2]:
                    clean_c = c[:70] + "..." if len(c) > 70 else c
                    print(f"    • {clean_c}")
            
            # Disclaimer check
            disclaimer = data.get('disclaimer', '')
            if disclaimer:
                print(f"\n  Disclaimer (first 60 chars): {disclaimer[:60]}...")
            
            # Language contamination check
            print(f"\n  Language Contamination Check:")
            answer_text = data.get('answer', '') + ' '.join(symptoms) + ' '.join(causes)
            
            has_fr_chars = any(c in answer_text for c in 'éèêëàâäûü')
            has_ar_chars = any('\u0600' <= c <= '\u06FF' for c in answer_text)
            
            if lang == 'en':
                if has_fr_chars:
                    print(f"    ⚠️  FRENCH CHARACTERS DETECTED (contamination!)")
                if has_ar_chars:
                    print(f"    ⚠️  ARABIC CHARACTERS DETECTED (contamination!)")
                if not has_fr_chars and not has_ar_chars:
                    print(f"    ✅ Pure English (no contamination)")
            
            elif lang == 'fr':
                if not has_fr_chars and len(answer_text) > 20:
                    print(f"    ⚠️  NO FRENCH CHARACTERS (possible contamination!)")
                else:
                    print(f"    ✅ French characters present (good)")
            
            elif lang == 'ar':
                if not has_ar_chars and len(answer_text) > 20:
                    print(f"    ⚠️  NO ARABIC CHARACTERS (possible contamination!)")
                else:
                    print(f"    ✅ Arabic characters present (good)")
        
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - backend not responding on {BASE_URL}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
    
    print("\n" + "="*70)
    print("✅ Multilingual validation test complete")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_multilingual()
