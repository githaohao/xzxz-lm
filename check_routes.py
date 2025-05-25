import sys
sys.path.append('backend')
from app.routes.voice import router

print('所有路由:')
for route in router.routes:
    if hasattr(route, 'path'):
        print(f"  {route.methods if hasattr(route, 'methods') else 'WebSocket'}: {route.path}")
    else:
        print(f"  {type(route)}: {route}")

print('\nWebSocket路由:')
ws_routes = [route for route in router.routes if hasattr(route, 'path') and 'ws' in route.path]
print(f"找到 {len(ws_routes)} 个WebSocket路由:")
for route in ws_routes:
    print(f"  {route.path}") 