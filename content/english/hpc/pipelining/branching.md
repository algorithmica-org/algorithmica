---
title: The Cost of Branching
weight: 2
---

### Branch Prediction

One more important thing to note is that conditional jumps may be very expensive. This is due to the fact that a modern CPU has a pretty deep "pipeline" or instructions on different stages of execution: some may be just loading from memory, some may be decoding, executing or writing the results. The whole process takes 12-15 cycles, not counting the latency of the operation itself, and you essentially "pay" these 12-15 cycles if you can't predict the next instruction you will be executing well in advance.

For example, consider the following loop that sums all odd numbers in an array:


```cpp
for (int i = 0; i < n; i++)
    if (a[i] & 1)
        s += a[i];
```

It can be implemented like this:

```nasm
loop:
    mov edx, DWORD PTR [rdi]
    mov ecx, edx  ; copy edx=a[i] into temporary register
    and ecx, 1    ; binary "and", and also sets ZF flag if the result is zero
    jne even      ; skip add if a[i] is even
    add eax, edx
even:
    add     rdi, 4
    cmp     rdi, rsi
    jne     loop
```

Modern CPUs are smart: they try to predict which branch is going to be taken. By default, the "don't jump" branch is always assumed, but during execution they keep statistics about branches taken on each instruction, and after a while and they start to predict them by recognizing common patterns.

This works well if the branch is predictable: for example, if all numbers in `a` are even or if 99% of the numbers are odd. This reduces the cost of a branch to almost zero, except for the check itself.

But if the parity of numbers in `a` is completely random, branch prediction will be wrong 50% of the time. Luckily, in simple cases like this, we can remove explicit branching completely by using a special `cmov` ("conditional move") instruction that assigns a value based on a condition:

```nasm
loop:
    mov     edx, DWORD PTR [rdi]
    add     ecx, rax, rdx  ; calculate sum in advance
    and     edx, 1
    cmovne  eax, ecx       ; execute assignment if a[i] is odd
    add     rdi, 4
    cmp     rdi, rsi
    jne     loop
```

This is roughly equivalent to:

```cpp
for (int i = 0; i < n; i++)
    s = (a[i] & 1 ? s + a[i]: s);
```

Branchless computing tricks like this one are especially important in all sorts of parallel algorithms.

---

Quiz 2. Есть массив случайных чисел от 0 до 99: 

for (int i = 0; i < N; i++)
    a[i] = rand() % 100;

и есть цикл, в котором суммируют все его элементы, меньшие 50:

for (int i = 0; i < N; i++)
    if (a[i] < 50)
        sum += a[i];

N = 1e6, цикл запускается много раз, а переменная sum помечена как volatile — то есть компилятор не может векторизовать цикл, объединить соседние итерации в одну, либо как-нибудь ещё считерить.

"if" и любой другой control flow — это как раз второй тип, и в случае с исходным циклом он проверяется на каждой итерации, создавая пробку из инструкций. Так как ифы исполняются часто, и с увеличением пайплайна эти пузыри стали серьёзной проблемой, производители процессоров добавили специальную инструкцию cmov ("conditional move"), которая позволяет по произвольному условию записать в переменную либо одно значение, либо другое — но не исполнять произвольный код. Когда мы заменяем явный if на тернарное условие в духе s += (cond ? x : 0), компилятор делает подобную оптимизацию, заменяя ветку на cmov.

Это примерно эквивалентно такому алгебраическому трюку:

sum += (a[i] < 50) * a[i];

---

cmov — это на самом деле не главная оптимизация бранчинга, которая есть в CPU. Гораздо более важную роль играет *branch prediction*: процессор может собирать статистики про определенные участки кода, на их основе предсказывать, какая ветка более вероятная, и сразу начать её исполнять (потому что почему бы нет). Если бранч предиктор угадал — то пузыря вообще не возникнет, не угадал — процессор просто выкинет все посчитанные результаты и начнет сначала.

То есть на самом деле не "if" стоит дорого, а предсказание неправильной ветки if-а стоит дорого. Если он хорошо предсказуем (с вероятностью 99% в этом случае), то оверхед у него будет совсем небольшой — в нашем случае это будет всего 1-2 цикла на проверку условия.

---

Аналогично, если бранч маловероятен, то его проверка тоже почти ничего не будет стоить. Поэтому всякие runtime exception-ы и проверки базовых случаев в фунциях на самом деле много не стоят.

---

Эвристическое правило, использующееся в компиляторах — если бранч можно предсказать с вероятностью 75% и выше, то следует его оставить, иначе использовать cmov. На большинстве архитектур, включая ту, на которой этот код исполнялся, как раз при соотношении 25/75% время исполнения уравнивается

---

Если массив отсортирован, то во время прохода по нему мы сначала половину итераций будем идти в левую ветку, а потом в правую. Этот паттерн очень хорошо улавливается бранч предиктором.

Важно отметить, что в таком случае цикл будет работать даже быстрее, чем вариант с cmov (и примерно за половину от времени 99%-цикла)  — потому что все проверки и все суммы можно исполнять как бы в отдельных «тредах»: не нужно ждать результата ифа, чтобы прибавить очередное значение к сумме.

---

Также если массив маленький, то бранч предиктор может просто запомнить результаты его сравнений полностью — и результат будет таким же, как и в случае с отсортированным массивом




50%: 13.9505
cmov: 7
sorted: 4+eps
small: 4-eps
vectorized: 0.32 (32 values per cycle: ~45x faster)
            0.5095 for large arrays (~25x)
            0.14 for small arrays (~100x)
            0.7 for 512?


---

```nasm
    mov     rcx, -4000000
    jmp     body
counter:
    add     rcx, 4
    jz      finished
body:
    mov     edx, dword ptr [rcx + a + 4000000]
    cmp     edx, 49
    jg      counter
    add     dword ptr [rsp + 12], edx
    jmp     counter
```

---

```nasm
mov     ecx, -4000000
; todo

mov     esi, dword ptr [rdx + a+4000000]
cmp     esi, 50
cmovge  esi, eax
add     dword ptr [rsp + 12], esi
add     rdx, 4
jne     .LBB0_4
```
---
