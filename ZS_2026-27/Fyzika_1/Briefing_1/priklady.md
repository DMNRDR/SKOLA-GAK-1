# Fyzika 1: Briefing 1, príklady na precvičenie

Postup: prečítaj zadanie → skús to sám (aspoň 5 min) → až potom rozbaľ **Riešenie**.
Učiteľove ručne písané riešenia cvičení 1 a 2 sú v `../Cvicenia/Cvicenie_1/` a `../Cvicenia/Cvicenie_2/`.

---

## Cvičenie 1

### 1. Ukáž, že amplitúda A v `y = A·sin(ωt + φ₀)` je maximálna výchylka.
<details><summary>Riešenie</summary>

Sínus nadobúda hodnoty od −1 po +1. Najväčšia hodnota y je teda `A·1 = A` → `y_max = A`.
</details>

### 2. Ukáž, že `T = 2π/ω`.
<details><summary>Riešenie</summary>

Za jednu periódu sa fáza zväčší o 2π (jeden „obeh“ sínusu):
`ω·(t + T) + φ₀ = ω·t + φ₀ + 2π` → `ω·T = 2π` → **`T = 2π/ω`**.
</details>

### 3. `y(t) = 0,2 cm · sin(4π rad·s⁻¹ · t − π/4 rad)`. Nájdi A, T, f, ω, φ₀ a y(0).
<details><summary>Riešenie</summary>

Porovnaj s tvarom `A·sin(ωt + φ₀)`:
- A = **0,2 cm**
- ω = **4π rad/s**
- f = ω/2π = **2 Hz**
- T = 1/f = **0,5 s**
- φ₀ = **−π/4 rad**
- y(0) = 0,2·sin(−π/4) = −0,2·(√2/2) ≈ **−0,14 cm**
</details>

### 4. `y(t) = ?·cos(? + ?)`: za 1 min vykoná 60 kmitov, max. záporná výchylka je −8 cm, fáza v t = 0 je 3π/2.
<details><summary>Riešenie</summary>

- f = N/t = 60/60 s = 1 Hz → ω = 2π rad/s
- A = **8 cm** (amplitúda je kladná!)
- φ₀ = 3π/2
- **`y = 8 cm · cos(2π s⁻¹ · t + 3π/2)`**, čo sa dá upraviť na `8 cm · sin(2π s⁻¹ · t)` (lebo `cos(x + 3π/2) = sin x`)
</details>

### 5. Pružiny k₁, k₂: výsledná tuhosť (a) za sebou, (b) vedľa seba?
<details><summary>Riešenie</summary>

- **(a) za sebou:** obidvoma ide tá istá sila, predĺženia sa sčítajú: `y = F/k₁ + F/k₂` → **`1/k = 1/k₁ + 1/k₂`** (výsledok je mäkší)
- **(b) vedľa seba:** predĺženie je rovnaké, sily sa sčítajú: `F = k₁y + k₂y` → **`k = k₁ + k₂`** (výsledok je tvrdší)

(Opačne ako pri odporoch v elektrine!)
</details>

---

## Cvičenie 2

### 1. Namerali sme |x| = 4·10⁻² m, |v| = 0,05 m/s, |a| = 0,8 m/s². Nájdi A, ω, T, v_max, a_max.
<details><summary>Riešenie</summary>

1. `a = −ω²·x` → `ω = √(|a|/|x|) = √(0,8/0,04) = √20 = 2√5 ≈ 4,47 rad/s`
2. `sin² + cos² = 1` → `(x/A)² + (v/(Aω))² = 1` → `A² = x² + v²/ω²`
   `A² = 16·10⁻⁴ + 0,0025/20 = 17,25·10⁻⁴ m²` → **A ≈ 4,15 cm**
3. `v_max = A·ω ≈ 0,0415 · 4,47 ≈` **0,19 m/s**
4. `a_max = A·ω² ≈ 0,0415 · 20 ≈` **0,83 m/s²**
5. `T = 2π/ω = π/√5 ≈` **1,4 s**
</details>

### 2. m = 0,1 kg, k = 10 N/m. Perióda?
<details><summary>Riešenie</summary>

`T = 2π·√(m/k) = 2π·√(0,01) = 0,2π ≈` **0,63 s**
</details>

### 3. Odvoď Eₚ a E pružinového oscilátora.
<details><summary>Riešenie</summary>

Práca potrebná na natiahnutie pružiny o y (sila rastie lineárne od 0 po k·y, teda plocha trojuholníka):
`Eₚ = ½·k·y²`
Celková energia: `E = Eₖ + Eₚ = ½mv² + ½ky²`. V krajnej polohe je v = 0 a y = A → **`E = ½·k·A²`**.
(Dá sa to overiť aj dosadením: `½m(Aω)²cos² + ½kA²sin²` a keďže `mω² = k`, vyjde `½kA²`.)
</details>

### 4. m = 100 g, v_max = 0,1 m/s, x_max = 1 cm. Tuhosť pružiny?
<details><summary>Riešenie</summary>

`ω = v_max / A = 0,1 / 0,01 = 10 rad/s` → `k = m·ω² = 0,1 · 100 =` **10 N/m**
(alebo cez energiu: `½mv_max² = ½kA²`)
</details>

### 5. E = 10 μJ, F_max = 1·10⁻³ N. Amplitúda?
*(Pozor: v zozname príkladov je E = 10 J, ale učiteľ to v riešení opravil na **10 μJ**.)*
<details><summary>Riešenie</summary>

`E = ½kA²`, `F_max = kA` → vydeľ: `E/F_max = ½A` → `A = 2E/F_max = 2·10·10⁻⁶ / 10⁻³ =` **0,02 m = 20 mm**
</details>

---

## Cvičenie 3 (príprava dopredu, riešenia zatiaľ nezverejnili)

### 6. Priamy tunel cez Zem Bratislava – Košice, vozeň bez trenia. Ako dlho trvá cesta? (R_Z = 6378 km, g ≈ 10 m/s²)
<details><summary>Riešenie</summary>

Vo vnútri Zeme gravitačná sila rastie lineárne so vzdialenosťou od stredu, takže jej zložka v smere tunela je `F = −(m·g/R)·x` (x = vzdialenosť od stredu tunela). To je presne **pružina** s `k = mg/R` → `ω = √(g/R)`.
Cesta z jedného konca na druhý je **polovica kmitu**:
`t = T/2 = π·√(R/g) = π·√(6 378 000/10) ≈ π·798,6 ≈ 2509 s ≈` **42 min**
Zaujímavosť: **nezávisí od dĺžky tunela**, takže Bratislava – Košice trvá rovnako ako Bratislava – Sydney.
</details>

### 7. Je `x = 3·sin(ωt) + 4·cos(ωt)` harmonické? Amplitúda a počiatočná fáza?
<details><summary>Riešenie</summary>

Áno (rovnaká ω). Chceme `A·sin(ωt + φ₀) = A·cos φ₀·sin ωt + A·sin φ₀·cos ωt`.
Porovnaj: `A·cos φ₀ = 3`, `A·sin φ₀ = 4`
→ **A = √(3² + 4²) = 5**, `tg φ₀ = 4/3` → **φ₀ ≈ 0,93 rad (53,1°)**
</details>

### 8. Kolmé kmity s periódami Tₓ, T_y. Aká je výsledná perióda a kedy vôbec existuje?
<details><summary>Riešenie</summary>

T musí byť celým násobkom oboch: `T = m·Tₓ = n·T_y` (m, n prirodzené) → T je **najmenší spoločný násobok**.
Existuje, len ak **`Tₓ/T_y = n/m` je racionálne číslo**. Inak sa krivka nikdy presne nezopakuje.
</details>

### 9. `x = A·sin(ωt)`, `y = A·cos(2ωt)`. Je pohyb periodický?
<details><summary>Riešenie</summary>

Pomer frekvencií je 1:2 (racionálny) → **áno**, s periódou `T = 2π/ω`.
Tvar: `cos 2α = 1 − 2sin²α` → `y = A·(1 − 2x²/A²)` → bod sa hýbe po **oblúku paraboly** pre x ∈ ⟨−A, A⟩.
</details>
