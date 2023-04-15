#include <stdio.h>
#include <lua.h>
#include <lauxlib.h>
#include <lualib.h>

int main(void) {
	float x = 2;
	float y;

	lua_State *L = luaL_newstate();
	luaL_openlibs(L);

	lua_pushnumber(L, x);
	lua_setglobal(L, "x");

	int ret = luaL_dostring(L, "y = math.pi * x");
	if (ret != LUA_OK) {
		printf("Error: %s\n", lua_tostring(L, -1));
		lua_pop(L, 1);
	}

	lua_getglobal(L, "y");
	y = lua_tonumber(L, -1);

	printf("Hello, world\n");
	printf("y = %.2f\n", y);

	lua_close(L);
	return 0;
}
