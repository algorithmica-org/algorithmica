---
title: Дискретное извлечение корня
authors:
- Максим Иванов
draft: true
---

Задача дискретного извлечения корня (по аналогии с задачей дискретного логарифма) звучит следующим образом. По данным n (n — простое), a, k требуется найти все x, удовлетворяющие условию:

 x^k \equiv a \pmod{n} 

Алгоритм решения
Решать задачу будем сведением её к задаче дискретного логарифма.

Для этого применим понятие Первообразного корня по модулю n. Пусть g — первообразный корень по модулю n (т.к. n — простое, то он существует). Найти его мы можем, как описано в соответствующей статье, за O( {\rm Ans} \cdot \log \phi(n) \cdot \log n) = O( {\rm Ans} \cdot \log^2 n) плюс время факторизации числа \phi(n).

Отбросим сразу случай, когда a=0 — в этом случае сразу находим ответ x=0.

Поскольку в данном случае (n — простое) любое число от 1 до n-1 представимо в виде степени первообразного корня, то задачу дискретного корня мы можем представить в виде:

 {\left( g^y \right)}^k \equiv a \pmod{n} 

где
 x \equiv g^y \pmod{n} 

Тривиальным преобразованием получаем:
 {\left( g^k \right)}^y \equiv a \pmod{n} 

Здесь искомой величиной является y, таким образом, мы пришли к задаче дискретного логарифмирования в чистом виде. Эту задачу можно решить алгоритмом baby-step-giant-step Шэнкса за O( \sqrt{n} \log n ), т.е. найти одно из решений y_0 этого уравнения (или обнаружить, что это уравнение решений не имеет).
Пусть мы нашли некоторое решение y_0 этого уравнения, тогда одним из решений задачи дискретного корня будет x_0 = g^{y_0} \pmod{n}.

Нахождение всех решений, зная одно из них
Чтобы полностью решить поставленную задачу, надо научиться по одному найденному x_0 = g^{y_0} \pmod{n} находить все остальные решения.

Для этого вспомним такой факт, что первообразный корень всегда имеет порядок \phi(n) (см. статью о первообразном корне), т.е. наименьшей степенью g, дающей единицу, является \phi(n). Поэтому добавление в показатель степени слагаемого с \phi(n) ничего не меняет:

 x^k \equiv g^{ y_0 \cdot k + l \cdot \phi(n) } \e[...]

Отсюда все решения имеют вид:
 x = g^{ y_0 + \frac{ l \cdot \phi(n) }{ k } } \pm[...]

где l выбирается таким образом, чтобы дробь \frac{ l \cdot \phi(n) }{ k } была целой. Чтобы эта дробь была целой, числитель должен быть кратен наименьшему общему кратному \phi(n) и k, откуда (вспоминая, что наименьшее общее кратное двух чисел {\rm lcm}(a,b) = \frac{ a \cdot b }{ {\rm gcd}(a,b) }), получаем:
 x = g^{ y_0 + i \frac{ \phi(n) }{ {\rm gcd}(k,\ph[...]

Это окончательная удобная формула, которая даёт общий вид всех решений задачи дискретного корня.
Реализация
Приведём полную реализацию, включающую нахождение первообразного корня, дискретное логарифмирование и нахождение и вывод всех решений.

int gcd (int a, int b) {
	return a ? gcd (b%a, a) : b;
}
 
int powmod (int a, int b, int p) {
	int res = 1;
	while (b)
		if (b & 1)
			res = int (res * 1ll * a % p),  --b;
		else
			a = int (a * 1ll * a % p),  b >>= 1;
	return res;
}
 
int generator (int p) {
	vector<int> fact;
	int phi = p-1,  n = phi;
	for (int i=2; i*i<=n; ++i)
		if (n % i == 0) {
			fact.push_back (i);
			while (n % i == 0)
				n /= i;
		}
	if (n > 1)
		fact.push_back (n);
 
	for (int res=2; res<=p; ++res) {
		bool ok = true;
		for (size_t i=0; i<fact.size() && ok; ++i)
			ok &= powmod (res, phi / fact[i], p) != 1;
		if (ok)  return res;
	}
	return -1;
}
 
int main() {
 
	int n, k, a;
	cin >> n >> k >> a;
	if (a == 0) {
		puts ("1\n0");
		return 0;
	}
 
	int g = generator (n);
 
	int sq = (int) sqrt (n + .0) + 1;
	vector < pair<int,int> > dec (sq);
	for (int i=1; i<=sq; ++i)
		dec[i-1] = make_pair (powmod (g, int (i * sq * 1ll * k % (n - 1)), n), i);
	sort (dec.begin(), dec.end());
	int any_ans = -1;
	for (int i=0; i<sq; ++i) {
		int my = int (powmod (g, int (i * 1ll * k % (n - 1)), n) * 1ll * a % n);
		vector < pair<int,int> >::iterator it =
			lower_bound (dec.begin(), dec.end(), make_pair (my, 0));
		if (it != dec.end() && it->first == my) {
			any_ans = it->second * sq - i;
			break;
		}
	}
	if (any_ans == -1) {
		puts ("0");
		return 0;
	}
 
	int delta = (n-1) / gcd (k, n-1);
	vector<int> ans;
	for (int cur=any_ans%delta; cur<n-1; cur+=delta)
		ans.push_back (powmod (g, cur, n));
	sort (ans.begin(), ans.end());
	printf ("%d\n", ans.size());
	for (size_t i=0; i<ans.size(); ++i)
		printf ("%d ", ans[i]);
 
}
