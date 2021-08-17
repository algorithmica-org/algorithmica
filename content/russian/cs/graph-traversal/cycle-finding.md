---
title: Нахождение цикла
author:
- Максим Иванов
---

Пусть дан ориентированный или неориентированный граф без петель и кратных рёбер. Требуется проверить, является ли он ациклическим, а если не является, то найти любой цикл.

Решим эту задачу с помощью поиска в глубину за O (M).

Алгоритм
Произведём серию поисков в глубину в графе. Т.е. из каждой вершины, в которую мы ещё ни разу не приходили, запустим поиск в глубину, который при входе в вершину будет красить её в серый цвет, а при выходе - в чёрный. И если поиск в глубину пытается пойти в серую вершину, то это означает, что мы нашли цикл (если граф неориентированный, то случаи, когда поиск в глубину из какой-то вершины пытается пойти в предка, не считаются).

Сам цикл можно восстановить проходом по массиву предков.

Реализация
Здесь приведена реализация для случая ориентированного графа.

int n;
vector < vector<int> > g;
vector<char> cl;
vector<int> p;
int cycle_st, cycle_end;

bool dfs (int v) {
	cl[v] = 1;
	for (size_t i=0; i<g[v].size(); ++i) {
		int to = g[v][i];
		if (cl[to] == 0) {
			p[to] = v;
			if (dfs (to))  return true;
		}
		else if (cl[to] == 1) {
			cycle_end = v;
			cycle_st = to;
			return true;
		}
	}
	cl[v] = 2;
	return false;
}

int main() {
	... чтение графа ...

	p.assign (n, -1);
	cl.assign (n, 0);
	cycle_st = -1;
	for (int i=0; i<n; ++i)
		if (dfs (i))
			break;

	if (cycle_st == -1)
		puts ("Acyclic");
	else {
		puts ("Cyclic");
		vector<int> cycle;
		cycle.push_back (cycle_st);
		for (int v=cycle_end; v!=cycle_st; v=p[v])
			cycle.push_back (v);
		cycle.push_back (cycle_st);
		reverse (cycle.begin(), cycle.end());
		for (size_t i=0; i<cycle.size(); ++i)
			printf ("%d ", cycle[i]+1);
	}
}
