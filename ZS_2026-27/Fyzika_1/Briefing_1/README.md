# Fyzika 1: Briefing 1 (Kmity)

> **Stav k 29. 9. 2026** · Prednášky: kapitola 1 *Kmity* (1.1 – 1.5) · Cvičenia 1 a 2 (+ cvičenie 3 ako ďalší krok)
> Zdroje: `../Prednasky/OsnovaSodpovedamiV3.pdf` (strany 1–16), `../Cvicenia/ZoznamPrikladov.pdf`, riešenia `../Cvicenia/Cvicenie_1`, `../Cvicenia/Cvicenie_2`

Postup: najprv prečítaj **ťahák** (1 obrazovka), potom **kapitoly 1–5** (pochopenie) a nakoniec si sám vyrieš **príklady** v [`priklady.md`](priklady.md). Riešenia sú tam schované, otvor ich až po vlastnom pokuse.

Na skúšku treba **aspoň 56 %** bodov. Celý semester: kmity → vlny → optika. Kmity sú základ, bez nich nepochopíš ani vlny.

---

## 0. Ťahák (nauč sa naspamäť)

| Čo | Vzorec | Jednotka |
|---|---|---|
| frekvencia | `f = 1/T` (počet kmitov za 1 s) | Hz = s⁻¹ |
| uhlová frekvencia | `ω = 2π·f = 2π/T` | rad·s⁻¹ |
| výchylka | `y = A·sin(ω·t + φ₀)` | m |
| rýchlosť | `v = A·ω·cos(ω·t + φ₀)` → `v_max = A·ω` | m·s⁻¹ |
| zrýchlenie | `a = −A·ω²·sin(ω·t + φ₀) = −ω²·y` → `a_max = A·ω²` | m·s⁻² |
| obnovovacia sila (pružina) | `F = −k·y` | N |
| pružinový oscilátor | `ω = √(k/m)`,  `T = 2π·√(m/k)` | |
| energia | `½·k·A² = ½·m·v² + ½·k·y²` (celková = kinetická + potenciálna) | J |
| amplitúda z x a v | `A² = x² + v²/ω²` | |
| ω zo zrýchlenia a výchylky | `ω = √(|a| / |x|)` | |
| rázy | `f_r = f₂ − f₁`,  `T_r = 1/(f₂ − f₁)` | |
| pružiny za sebou | `1/k = 1/k₁ + 1/k₂` | |
| pružiny vedľa seba | `k = k₁ + k₂` | |

**Najčastejšie chyby:**
- **Amplitúda je vždy kladná.** Ak je „maximálna záporná výchylka −8 cm“, potom A = 8 cm.
- `ω ≠ f`. Keď máš f = 2 Hz, tak ω = 4π rad/s (nie 2).
- Kalkulačku prepni na **radiány** (RAD, nie DEG).
- Jednotky: cm → m, g → kg, min → s.

---

## 1. Základné pojmy (prednáška 1.1)

- **Kmitanie** je pohyb, ktorý sa (približne) opakuje. **Mechanické kmitanie** = kmitá poloha nejakého telesa (hmotného bodu, HB).
- **Periodické kmitanie** sa opakuje **presne**. Podmienka: `P(t) = P(t + T)`, t. j. po uplynutí jednej periódy je teleso na tom istom mieste.
- **Perióda T** je čas jedného kmitu [s].
- **Frekvencia f** je počet kmitov za sekundu [Hz]. `f = 1/T`.
  - Príklad: T = 5 s → f = 1/5 = 0,2 Hz, teda za 1 s prebehne 0,2 kmitu.

## 2. Prečo vôbec niečo kmitá? Dynamika (1.2)

- **Obnovovacia sila** ťahá teleso späť do **rovnovážnej polohy**. Má **opačný smer ako výchylka** a závisí od nej.
- **Rovnovážna poloha** je miesto, kde je obnovovacia sila nulová.
- Príklady:
  - pružina: `F = −k·y` (k = tuhosť pružiny [N/m]). Mínus hovorí: vychýlim doprava, sila ťahá doľava.
  - gravitácia: `F = −G·M·m/r³ · r⃗` (Zem okolo Slnka)

> **Intuícia:** Teleso prestrelí rovnovážnu polohu (lebo má rýchlosť), sila ho zabrzdí, vráti ho späť, znova prestrelí… a tak kmitá.

## 3. Jednoduché harmonické kmitanie (1.3), NAJDÔLEŽITEJŠIE

```
          y  =  A · sin( ω·t + φ₀ )
          │     │        │     │
   okamžitá  amplitúda  uhlová  počiatočná
   výchylka            frekv.  fáza
                   └─────────────┘
                   fáza φ(t)
```

| Pojem | Čo to je |
|---|---|
| **okamžitá výchylka y** | kde je teleso v čase t (vzdialenosť od rovnovážnej polohy, môže byť aj záporná) |
| **amplitúda A** | maximálna výchylka, **vždy kladná** |
| **uhlová frekvencia ω** | `2π·f`. Jeden kmit = uhol 2π. 5 kmitov/s → za 1 s narastie uhol o 10π → ω = 10π rad/s |
| **fáza φ(t)** | celé to, čo je v sínuse: `ω·t + φ₀` [rad] |
| **počiatočná fáza φ₀** | fáza v čase t = 0. Posúva graf sínusu doľava |

**Ako si to predstaviť: kružnica.** Bod obieha po kružnici s polomerom A uhlovou rýchlosťou ω. Jeho **tieň na zvislej osi** kmitá harmonicky:
- výchylka tieňa = `A·sin φ`
- rýchlosť tieňa = zložka obvodovej rýchlosti `A·ω` → `A·ω·cos φ`
- zrýchlenie tieňa = zložka dostredivého zrýchlenia `A·ω²` → `−A·ω²·sin φ`

Preto:
- **v rovnovážnej polohe** (y = 0): rýchlosť je **maximálna**, zrýchlenie je **nulové**
- **v krajnej polohe** (y = ±A): rýchlosť je **nulová**, zrýchlenie je **maximálne** (a smeruje dnu)

> Keď vieš derivovať: `v = dy/dt`, `a = dv/dt`. Z derivácie sínusu dostaneš presne tie vzorce vyššie.

**Sínus vs. kosínus.** Obe sú harmonické, líšia sa len fázou: `cos(x) = sin(x + π/2)`, `cos(x + 3π/2) = sin(x)`. (Presne takto to učiteľ upravil v príklade 1.4.) Vzorce na úpravy sú v `../Cvicenia/GoniometrickeVzorce.pdf`.

### Pružinový harmonický oscilátor (PHO)
Závažie hmotnosti m na pružine s tuhosťou k:
- `ω = √(k/m)` → `T = 2π·√(m/k)` (tvrdšia pružina → rýchlejšie kmity, ťažšie závažie → pomalšie)

### Energia PHO
```
½·k·A²   =   ½·m·v²   +   ½·k·y²
celková      kinetická     potenciálna
(konštanta)  (max v strede) (max v krajnej polohe)
```
Energia sa **prelieva** medzi kinetickou a potenciálnou, **súčet sa nemení** (amplitúda je konštantná).

## 4. Skladanie kmitov v jednom smere (1.4)

Dve kmitania na tej istej osi sa jednoducho **sčítajú**: `y₃ = y₁ + y₂`.

| Prípad | Výsledok |
|---|---|
| **rovnaké frekvencie** | opäť **harmonické** kmitanie |
| ↳ **synfázne** (rovnaká fáza) | kmity sa **zosilnia**: `A = A₁ + A₂` |
| ↳ **protifázne** (fázy sa líšia o π) | kmity sa **zoslabia**: `A = |A₁ − A₂|` |
| **rôzne frekvencie** | výsledok **NIE JE** harmonický |
| ↳ **blízke** frekvencie → **RÁZY** | amplitúda pomaly „dýcha“. `f_r = f₂ − f₁` |

> **Rázy v praxi:** tóny 300 Hz a 301 Hz spolu → počuješ zosilňovanie a zoslabovanie 1× za sekundu. Pri 300 Hz + 302 Hz je to 2× za sekundu.

**Trik (príklad 7):** `a·sin(ωt) + b·cos(ωt)` je harmonické s `A = √(a² + b²)` a `tg φ₀ = b/a`.

## 5. Skladanie kolmých kmitov (1.5)

x kmitá vodorovne, y zvisle. Bod kreslí v rovine krivku.

| Frekvencie | Fázový rozdiel `φ₀y − φ₀x` | Výsledná krivka |
|---|---|---|
| rovnaké | 0 (synfázne) | **úsečka** (šikmo /) |
| rovnaké | ±π (protifázne) | **úsečka** (šikmo \\) |
| rovnaké | ±π/2 a `Aₓ = A_y` | **kružnica** |
| rovnaké | čokoľvek iné | **elipsa** (kružnica aj úsečka sú špeciálne elipsy) |
| v pomere prirodzených čísel (2:1, 3:1, 5:7…) | – | **Lissajousove krivky** |

> Výsledný pohyb je **periodický iba vtedy**, keď je pomer periód `Tₓ/T_y` **racionálne číslo**. Výsledná perióda je potom najmenší spoločný násobok Tₓ a T_y.

---

## Čo nasleduje (aby ťa to neprekvapilo)
- **Cvičenie 3:** príklady 6–9 (tunel cez Zem, `3 sin + 4 cos`, kolmé kmity). Sú v [`priklady.md`](priklady.md).
- **Prednášky:** kapitola 2 *Vlny* (vlnová dĺžka, rýchlosť šírenia, stojaté vlnenie, Dopplerov jav…). Z toho bude Briefing 2.

## Kontrolné otázky (odpovedz si nahlas bez pozerania)
1. Aký je rozdiel medzi f a ω a ako ich prepočítam?
2. Kde má oscilátor najväčšiu rýchlosť a kde najväčšie zrýchlenie? Prečo?
3. Prečo je v `F = −k·y` mínus?
4. Čo sa deje s energiou počas jedného kmitu?
5. Čo vznikne zložením dvoch kmitov s rovnakou frekvenciou? A s blízkymi frekvenciami?
6. Kedy zložením kolmých kmitov vznikne kružnica?
