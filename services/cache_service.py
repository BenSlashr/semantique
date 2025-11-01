"""
Service de cache unifié pour l'application SEO Analyzer
Supporte Redis (recommandé) et fallback mémoire
"""
import json
import time
import hashlib
from typing import Any, Dict, Optional, Union
from config import settings

class CacheService:
    """Service de cache unifié avec fallback mémoire"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_enabled = settings.ENABLE_CACHE
        self.ttl = settings.CACHE_TTL
        
        # Essai d'initialisation Redis
        if self.cache_enabled:
            self._init_redis()
    
    def _init_redis(self):
        """Initialise Redis si disponible"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test de connexion
            self.redis_client.ping()
            print("✅ Cache: Redis connecté")
        except Exception as e:
            print(f"⚠️ Cache: Redis indisponible ({e}), utilisation mémoire")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Génère une clé de cache unique"""
        # Combine tous les arguments en string
        key_data = f"{prefix}:" + ":".join(str(arg) for arg in args)
        if kwargs:
            key_data += ":" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        # Hash MD5 pour clé courte et unique
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if not self.cache_enabled:
            return None
            
        key = self._generate_key(prefix, *args, **kwargs)
        
        try:
            if self.redis_client:
                # Cache Redis
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Cache mémoire
                if key in self.memory_cache:
                    cached_item = self.memory_cache[key]
                    # Vérifier expiration
                    if time.time() < cached_item['expires_at']:
                        return cached_item['data']
                    else:
                        # Supprimer item expiré
                        del self.memory_cache[key]
        except Exception as e:
            print(f"🚨 Cache: Erreur lecture {key[:8]}: {e}")
        
        return None
    
    def set(self, prefix: str, value: Any, *args, **kwargs) -> bool:
        """Stocke une valeur dans le cache"""
        if not self.cache_enabled:
            return False
            
        key = self._generate_key(prefix, *args, **kwargs)
        
        try:
            if self.redis_client:
                # Cache Redis
                data = json.dumps(value, ensure_ascii=False)
                self.redis_client.setex(key, self.ttl, data)
                print(f"💾 Cache Redis: {key[:8]} → {len(str(value))[:5]} caractères")
            else:
                # Cache mémoire
                self.memory_cache[key] = {
                    'data': value,
                    'expires_at': time.time() + self.ttl
                }
                # Nettoyage périodique (garde max 1000 items)
                if len(self.memory_cache) > 1000:
                    self._cleanup_memory_cache()
                print(f"💾 Cache mémoire: {key[:8]} → {len(str(value))[:5]} caractères")
            
            return True
            
        except Exception as e:
            print(f"🚨 Cache: Erreur écriture {key[:8]}: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Nettoie le cache mémoire des items expirés"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.memory_cache.items()
            if current_time >= item['expires_at']
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        print(f"🧹 Cache: {len(expired_keys)} items expirés supprimés")
    
    def delete(self, prefix: str, *args, **kwargs) -> bool:
        """Supprime une valeur du cache"""
        if not self.cache_enabled:
            return False
            
        key = self._generate_key(prefix, *args, **kwargs)
        
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
        except Exception as e:
            print(f"🚨 Cache: Erreur suppression {key[:8]}: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Vide tout le cache"""
        if not self.cache_enabled:
            return False
            
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            
            print("🧹 Cache: Tout le cache vidé")
            return True
            
        except Exception as e:
            print(f"🚨 Cache: Erreur vidage: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        if not self.cache_enabled:
            return {"enabled": False}
        
        stats = {
            "enabled": True,
            "ttl_days": self.ttl // (24 * 3600),
            "backend": "redis" if self.redis_client else "memory"
        }
        
        try:
            if self.redis_client:
                info = self.redis_client.info()
                stats.update({
                    "keys_count": self.redis_client.dbsize(),
                    "memory_usage_mb": info.get('used_memory', 0) / (1024 * 1024)
                })
            else:
                current_time = time.time()
                valid_items = sum(
                    1 for item in self.memory_cache.values()
                    if current_time < item['expires_at']
                )
                stats.update({
                    "keys_count": valid_items,
                    "total_items": len(self.memory_cache)
                })
        except Exception as e:
            stats["error"] = str(e)
        
        return stats

# Instance globale
cache_service = CacheService()

# Fonctions utilitaires pour les services
def cache_serp_results(query: str, location: str = "France", language: str = "fr", num_results: int = 20):
    """Décorateur pour cache des résultats SERP"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Tentative de récupération du cache
            cached = cache_service.get("serp", query, location, language, num_results)
            if cached is not None:
                print(f"📦 Cache HIT: SERP '{query}'")
                return cached
            
            # Exécution et mise en cache
            result = await func(*args, **kwargs)
            if result:
                cache_service.set("serp", result, query, location, language, num_results)
                print(f"💾 Cache MISS: SERP '{query}' → stocké")
            
            return result
        return wrapper
    return decorator

def cache_seo_analysis(query: str):
    """Décorateur pour cache des analyses SEO"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Tentative de récupération du cache
            cached = cache_service.get("seo_analysis", query)
            if cached is not None:
                print(f"📦 Cache HIT: Analyse SEO '{query}'")
                return cached
            
            # Exécution et mise en cache
            result = await func(*args, **kwargs)
            if result:
                cache_service.set("seo_analysis", result, query)
                print(f"💾 Cache MISS: Analyse SEO '{query}' → stocké")
            
            return result
        return wrapper
    return decorator

def cache_page_content(url: str):
    """Décorateur pour cache du contenu des pages"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Tentative de récupération du cache
            cached = cache_service.get("content", url)
            if cached is not None:
                print(f"📦 Cache HIT: Contenu {url[:50]}...")
                return cached
            
            # Exécution et mise en cache
            result = await func(*args, **kwargs)
            if result and result.get('word_count', 0) > 0:
                cache_service.set("content", result, url)
                print(f"💾 Cache MISS: Contenu {url[:50]}... → stocké")
            
            return result
        return wrapper
    return decorator