# DayZ IK1H Import → DayZ Solve → Blender IK Authoring Plan

## 1. Мета

Після чистого імпорту базової анімації та IK1H `.anm` Blender повинен:

1. Відтворити початкову праву руку за тим самим порядком даних, який
   використовує DayZ.
2. Лише після отримання готової DayZ-пози створити Blender IK controls точно
   поверх цієї пози, без стрибка або зміни руки.
3. Дозволити редагувати кисть і лікоть через Blender IK.
4. Дозволити вільно повертати кисть, не повертаючи разом із нею helper-напрям
   передпліччя.
5. Під час Bake перерахувати відредаговану Blender-позу назад у правильні
   DayZ helper-треки та експортувати IK1H ANM.

Ключова вимога authoring: користувач може незалежно повертати `RightHand`.
Поворот кисті змінює орієнтацію кисті, пальців і предметного базису, але не
повертає геометричну напрямну передпліччя та не змінює положення ліктя.

Цільовий pipeline:

```text
Base ANM
   ↓
IK1H ANM raw tracks
   ↓
DayZ-compatible decode + solve
   ↓
готова DayZ-поза
   ↓
Blender IK, ініціалізований із готової пози
   ↓
редагування
   ↓
Bake назад у DayZ helper-треки
   ↓
IK1H ANM export
```

## 2. Головні інваріанти

### 2.1. Helper-напрям руки

Видима helper-напрямна завжди визначається геометрією розв'язаної руки:

```text
helper_start = wrist position
helper_end   = elbow position
helper_axis  = normalize(helper_end - helper_start)
```

`RightHand.rotation` у цю формулу не входить.

Це правило стосується evaluated/display guide у Blender. Воно не означає, що
локальні quaternion/translation сирих ANM helper-треків завжди залишаються
чисельно незмінними. Під час Bake вони можуть і повинні компенсувати новий
поворот primary target, щоб після runtime-композиції DayZ відновив той самий
world-space напрям wrist→elbow.

### 2.2. Обертання кисті

Коли змінюється лише `CTRL_RightHand.rotation`:

- `RightHand` обертається;
- пальці обертаються разом із кистю;
- предмет, прикріплений до кисті, обертається разом із кистю;
- wrist position не змінюється;
- elbow position не змінюється;
- helper positions не змінюються;
- helper-напрям wrist→elbow не змінюється;
- helper-и не успадковують twist кисті.

### 2.3. Переміщення руки

Коли змінюється `CTRL_RightHand.location` або `CTRL_RightElbow`:

- Blender IK перебудовує руку;
- helper_start слідує за wrist;
- helper_end слідує за elbow;
- helper-напрям перебудовується вздовж нового передпліччя.

### 2.4. Import/Build invariant

Створення Blender control rig після DayZ solve не має змінити:

- `RightArm`;
- `RightArmRoll`;
- `RightForeArm`;
- `RightForeArmRoll`;
- `RightHand`;
- wrist position/rotation;
- elbow position;
- `RightHand_Dummy`;
- пальці.

## 3. Підтверджені runtime-семантики DayZ

### 3.1. Правий ланцюг

```text
RightArm
→ RightArmRoll
→ RightForeArm
→ RightForeArmRoll
→ RightHand
```

### 3.2. Helper mapping

```text
ikpose_chainoffset       = RightHandOrigin
ikpose_chainmiddledir    = RightForeArmDirection
ikpose_chainmiddlediro   = RightHandOrigin,
                           RightForeArmDirectionOrigin
ikpose_weaponoffset      = RightHand_Dummy
```

### 3.3. Primary target

`RightHandOrigin` у сирому ANM не є абсолютною Blender world transform.

```text
currentEnd     = evaluated RightHand після base + IK RightHand track
rawChainOffset = raw RightHandOrigin
chainOffset    = inverse(rawChainOffset)
primaryTarget  = currentEnd * chainOffset
```

`primaryTarget` задає target position і target rotation кисті.

### 3.4. Elbow inputs

```text
RightHandOrigin ↔ RightForeArmDirectionOrigin
    = опорна пара для middle-chain solve

RightForeArmDirection
    = preferred middle direction / pole input
```

Helper-пара є входом початкового DayZ solve. Після переходу в режим Blender
authoring видима helper-напрямна стає відображенням фактичної геометрії
wrist–elbow, а raw ANM helpers перераховуються лише під час Bake.

Отже, не можна ототожнювати:

```text
raw RightHandOrigin / RightForeArmDirectionOrigin з ANM
    !=
їхня видима world-space напрямна у Blender
```

На імпорті raw helper-и спочатку декодуються у runtime inputs, DayZ-compatible
solve будує анатомічну руку, і лише з уже розв'язаної руки створюється видима
напрямна wrist→elbow.

## 4. Необхідне розділення даних

Одна Blender-кістка не повинна одночасно бути:

- сирим runtime offset із ANM;
- видимою wrist–elbow напрямною;
- animator control;
- дочірньою кісткою кисті.

Потрібно розділити три рівні.

### 4.1. Raw DayZ layer

Приховані або збережені в metadata transforms:

```text
RAW_RightHandOrigin
RAW_RightForeArmDirectionOrigin
RAW_RightForeArmDirection
RAW_RightHand_Dummy
```

Вони потрібні для точного decode, початкового solve та Bake/export.

### 4.2. Animator controls

```text
CTRL_RightHand
CTRL_RightElbow
IK_RightHandDummy.R
```

- `CTRL_RightHand.location` керує wrist target.
- `CTRL_RightHand.rotation` керує лише орієнтацією кисті.
- `CTRL_RightElbow` керує площиною згину.
- `IK_RightHandDummy.R` керує положенням предмета.

### 4.3. Display/diagnostic guide

Видима пара, що показує фактичне передпліччя:

```text
GUIDE_RightHandOrigin
GUIDE_RightForeArmDirectionOrigin
```

Якщо для сумісності UI мають залишитися назви `RightHandOrigin` та
`RightForeArmDirectionOrigin`, їхні видимі transforms повинні працювати як
GUIDE layer, а raw значення мають зберігатися окремо.

## 5. Етап A — чистий Base ANM import

Файл реалізації:

`DayzAnimationToolsBinary/Import/ImportAnm.py`

1. Очистити попередні actions, NLA strips, authoring constraints і control rig.
2. Імпортувати базову анімацію, наприклад:

   ```text
   p_1hd_erc_idle_low.anm
   ```

3. Для бази:

   - rotation keys увімкнені;
   - translation keys вимкнені;
   - scale keys вимкнені;
   - Blender IK вимкнений.

4. Зберегти evaluated base matrices правого й лівого ланцюгів на кадрах 0–1.

## 6. Етап B — raw IK1H import

1. Визначати IK1H за наявністю helper-треків, а не лише за станом UI-галки:

   ```text
   RightHandOrigin
   RightForeArmDirectionOrigin
   RightForeArmDirection
   RightHand_Dummy
   ```

2. Завантажити перші два службові кадри.
3. Завантажити translation та rotation для всіх IK1H-треків.
4. Не створювати Blender IK до завершення DayZ decode + solve.
5. Зберігати сирі engine-space значення окремо від Blender display matrices.

## 7. Етап C — застосування `RightHand` track

До WeaponIK solve необхідно застосувати трек `RightHand` із IK1H ANM поверх
базової анімації.

Результат:

```text
currentEnd = evaluated RightHand
```

Заборонено використовувати замість `currentEnd`:

- rest pose;
- лише base action без IK `RightHand` track;
- matrix після вже активованого Blender IK;
- matrix після authoring constraints.

## 8. Етап D — DayZ decode

### 8.1. `RightHandOrigin`

1. Декодувати raw transform.
2. Застосувати cache-loader inverse.
3. Побудувати:

   ```text
   primaryTarget = currentEnd * inverse(rawRightHandOrigin)
   ```

4. Не підміняти primaryTarget видимою Blender helper-кісткою.

### 8.2. Right elbow helpers

Декодувати:

```text
RightForeArmDirectionOrigin
RightForeArmDirection
```

Побудувати runtime inputs:

```text
primaryMiddleOriginA
primaryMiddleOriginB
primaryMiddleDirection
```

Axis conversion має бути підтверджений окремим importer-vs-runtime тестом.
Заборонено оцінювати правильність лише за однаковою rotation двох helper bones.

## 9. Етап E — DayZ-compatible solve

Файл реалізації:

`DayzAnimationTools/Utils/WeaponIKSolver.py`

Вхід:

```text
base/evaluated right chain
primaryTarget
primaryMiddleOriginA
primaryMiddleOriginB
primaryMiddleDirection
```

Solver повинен:

1. Зберегти довжини плеча й передпліччя.
2. Поставити `RightHand` на `primaryTarget`.
3. Побудувати положення ліктя з DayZ helper-входів.
4. Стабілізувати `RightArmRoll` і `RightForeArmRoll`.
5. Застосувати target rotation до `RightHand` окремо від elbow-plane solve.
6. Не дозволяти wrist twist змінювати вже визначену площину ліктя.

## 10. Етап F — пальці, предмет і ліва рука

### 10.1. Пальці

Після правого solve застосувати right-finger rotations. Пальці не впливають на
плече, лікоть або wrist target.

### 10.2. Предмет

```text
weaponBase = primaryTarget * rawRightHandDummy
```

### 10.3. Ліва рука

Після побудови `weaponBase`:

```text
secondaryTarget = weaponBase * LeftHandIKTarget
```

Потім розв'язати лівий ланцюг із:

```text
LeftHandOrigin
LeftForeArmDirectionOrigin
LeftForeArmDirection
```

## 11. Етап G — створення Blender IK поверх DayZ-пози

Файл реалізації:

`DayzAnimationTools/Tools/AddSurvivorIK.py`

1. До створення рігу зберегти object-space matrices готової DayZ-пози.
2. Створити proxy chain:

   ```text
   MCH_RightArm_IK
   MCH_RightForeArm_IK
   MCH_RightHand_IK
   ```

3. Ініціалізувати proxy chain точно з DayZ solved matrices.
4. Створити:

   ```text
   CTRL_RightHand = solved RightHand target
   CTRL_RightElbow = solved DayZ elbow/pole state
   ```

5. Увімкнути Blender IK лише після ініціалізації controls.
6. Після ввімкнення порівняти всі chain matrices із збереженим DayZ snapshot.
7. Якщо будь-яка matrix змінилася понад epsilon — Build вважається невдалим.

## 12. Етап H — незалежна forearm guide sync

Додати окрему функцію, наприклад:

```python
sync_right_forearm_guide(arm, control_rig)
```

Вона виконується після Blender IK evaluation:

```text
wrist = evaluated wrist joint position
elbow = evaluated elbow joint position
axis  = normalize(elbow - wrist)
```

Функція повинна:

1. Поставити guide start у wrist.
2. Поставити guide end у elbow.
3. Побудувати rotation guide із wrist→elbow.
4. Використати стабільний roll від площини руки/pole control.
5. Не читати `CTRL_RightHand.rotation` для визначення guide axis.
6. Не створювати parent/Copy Rotation залежність від кисті.

Виклики:

- після початкового DayZ solve;
- після Build;
- у `depsgraph_update_post` після proxy sync;
- у `frame_change_post`;
- перед Bake;
- після зміни `CTRL_RightHand` або `CTRL_RightElbow`.

## 13. Constraint/parenting rules

Заборонено:

```text
GUIDE_RightHandOrigin.parent = CTRL_RightHand
GUIDE_RightForeArmDirectionOrigin.parent = CTRL_RightHand
Copy Rotation від CTRL_RightHand до guide
Copy Transforms від CTRL_RightHand до всієї guide-пари
```

Допустимо:

- direct matrix sync після evaluated IK;
- Copy Location лише для wrist anchor, якщо це не створює cycle;
- окремий guide carrier, rotation якого будується з wrist→elbow;
- hidden raw/export controls без візуальної authoring ролі.

## 14. Етап I — authoring behavior

### 14.1. `CTRL_RightHand.location`

- переміщує wrist target;
- Blender IK перебудовує руку;
- guide перебудовується за новими wrist/elbow positions.

### 14.2. `CTRL_RightHand.rotation`

- повертає тільки кисть;
- не змінює wrist location;
- не змінює elbow location;
- не змінює world guide axis;
- повертає пальці та предметний базис.

### 14.3. `CTRL_RightElbow`

- змінює площину згину;
- змінює evaluated elbow position;
- guide end слідує за новим elbow;
- wrist залишається на hand target.

## 15. Етап J — Bake назад у DayZ

### 15.1. `RightHandOrigin`

З поточного authoring target:

```text
desiredTarget = CTRL_RightHand
currentEnd    = evaluated base + IK RightHand track до WeaponIK
chainOffset   = inverse(currentEnd) * desiredTarget
rawRightHandOrigin = inverse(chainOffset)
```

Потім застосовується підтверджене engine/Blender axis encoding.

### 15.2. Elbow helpers

Зчитати:

```text
wristPosition
elbowPosition
polePosition
primaryTarget
```

Побудувати world guide незалежно від wrist twist і перетворити його назад у
локальні runtime helper-значення.

Критичний випадок:

- якщо змінилася лише `CTRL_RightHand.rotation`, world guide залишається тим
  самим;
- локальний raw helper-вектор має компенсувати нову target rotation;
- після множення в DayZ відновлюється той самий world elbow guide.

Заборонено під час Bake напряму копіювати world matrices
`GUIDE_RightHandOrigin` / `GUIDE_RightForeArmDirectionOrigin` у сирі helper
кістки. Encoder повинен виконати обернене runtime-перетворення від бажаного
world-space wrist/elbow state до ANM-local helper values.

### 15.3. `RightHand_Dummy`

```text
rawDummy = inverse(primaryTarget) * desiredWeaponBase
```

Rotation кисті не повинна застосуватися до dummy двічі.

### 15.4. Службові кадри

Записати однакову статичну IK1H позу на кадри 0 і 1:

- translation keys для всіх необхідних IK1H tracks;
- rotation keys;
- пальці;
- helpers;
- dummy.

## 16. Export rules

Файл реалізації:

`DayzAnimationToolsBinary/Export/ExportAnm.py`

1. Експортувати основний `_DayZ_Character`, а не control/proxy rig.
2. Не використовувати visible guide matrices як сирі ANM transforms напряму.
3. Використовувати результати Bake/encoding.
4. Не відновлювати старий imported raw helper після редагування руки.
5. Не застосовувати wrist rotation до elbow guide двічі.
6. Не застосовувати wrist rotation до `RightHand_Dummy` двічі.

## 17. Автоматизовані тести

### 17.1. Clean import test

```text
clean template
→ base import
→ box_cereal import
→ DayZ solve
```

Перевірити:

- primaryTarget;
- wrist position/rotation;
- elbow position;
- roll bones;
- raw helper decode;
- відсутність helper-ів у животі.

### 17.2. Build no-jump test

Порівняти chain matrices:

```text
DayZ solved pose
vs
pose immediately after Build IK1 Controls
```

### 17.3. Wrist rotation isolation test

1. Зберегти wrist, elbow та guide world transforms.
2. Повернути `CTRL_RightHand` на 90° без translation.
3. Перевірити:

   ```text
   RightHand rotation changed       = true
   wrist position changed           = false
   elbow position changed           = false
   guide start/end changed          = false
   guide axis changed               = false
   ```

### 17.4. Hand translation test

1. Перемістити `CTRL_RightHand`.
2. Перевірити:

   - wrist слідує target;
   - elbow вирішується через pole;
   - guide слідує wrist–elbow;
   - segment lengths не змінюються.

### 17.5. Elbow control test

1. Перемістити `CTRL_RightElbow`.
2. Перевірити:

   - wrist target незмінний;
   - elbow position змінений;
   - guide end слідує elbow;
   - guide axis оновлений.

### 17.6. Bake no-jump test

Порівняти перед/після Bake:

- wrist;
- wrist rotation;
- elbow;
- roll bones;
- пальці;
- dummy;
- guide.

### 17.7. Export/reimport test

```text
edited Blender pose
→ Bake
→ Export
→ clean template
→ base import
→ exported IK import
→ DayZ solve
```

Порівняти всі ключові matrices із вихідною edited pose.

## 18. Візуальна перевірка

Для кожного важливого етапу зробити OpenGL screenshot:

- без назв кісток;
- без custom shapes;
- Front View;
- Side View;
- крупний wrist–elbow план.

На знімку має бути очевидно:

```text
guide_start лежить на wrist
guide_end лежить на elbow
guide_axis лежить уздовж передпліччя
```

Окремий screenshot після повороту кисті на 90° повинен показати:

- кисть повернута;
- helper-напрямна залишилася на тому самому місці вздовж руки.

## 19. Перевірка в DayZ

Остаточним доказом є in-game результат:

1. Початковий `box_cereal` після чистого імпорту збігається з DayZ.
2. Після зміни hand location рука збігається з Blender.
3. Після зміни wrist rotation кисть збігається з Blender, а лікоть не
   перевертається.
4. `RightHand_Dummy` і предмет збігаються з Blender.
5. Немає розтягування плеча або зміни довжини сегментів.

## 20. Послідовність реалізації

1. Зафіксувати поточний стан окремими failing tests і screenshots. **Виконано.**
2. Прибрати provisional/непідтверджені importer axis-правки, якщо вони не
   підтверджуються runtime-тестом.
3. Розділити raw runtime data, animator controls і visible guide. **Виконано.**
4. Виправити base + IK `RightHand` pre-solve evaluation. **Виконано для
   поточного clean-import тесту.**
5. Виправити decode `RightHandOrigin` і elbow helper inputs. **Decode працює
   для поточного `box_cereal`; encoder ще не симетричний після wrist twist.**
6. Довести DayZ-compatible primary solve без Blender IK. **Виконано для
   поточного тестового файла з похибкою wrist приблизно `1.2e-7`.**
7. Побудувати Blender IK поверх solved snapshot без стрибка. **Виконано для
   поточного тесту; elbow error приблизно `1.2e-5`.**
8. Додати незалежний wrist–elbow guide sync. **Виконано.**
9. Додати wrist rotation isolation test. **Виконано; guide start/end/axis не
   змінюються при тестовому twist кисті.**
10. Виправити Bake encoding `RightHandOrigin`: зараз поворот
    `CTRL_RightHand` не потрапляє у raw exported target у round-trip тесті.
11. Виправити/перевірити обернене runtime-кодування elbow helpers і dummy,
    не копіюючи display guide напряму у raw tracks.
12. Провести export/reimport regression до збігу target, анатомічного ланцюга,
    helpers і `RightHand_Dummy` у межах epsilon.
13. Зробити візуальну перевірку.
14. Перевірити експорт у DayZ.
15. Лише після in-game підтвердження перенести встановлені факти в
    `IK1H_GROUND_TRUTH.md`.

### 20.1. Поточний зафіксований блокер

Regression:

```text
tools/test_ik1h_dayz_solve_blender_guide_roundtrip.py
```

Стан:

- clean import, solve, Build no-jump, wrist-twist isolation, hand/pole move та
  Bake no-jump проходять;
- export/reimport після повороту кисті не проходить;
- `RightHandOrigin` у raw export лишається близьким до імпортованого значення,
  тому губиться приблизно `0.60 rad` відредагованого wrist rotation;
- `RightHand_Dummy` після циклу також має велику помилку, яку треба перевірити
  після виправлення primary target, щоб не маскувати похідну помилку окремим
  патчем.

Наступна діагностика повинна знайти точне місце втрати transform:

```text
CTRL_RightHand
→ IK_RightHandOrigin.R export control
→ main RightHandOrigin baked keys
→ ExportAnm.GetBoneLocation/GetBoneRotation
→ raw ANM RightHandOrigin
```

Виправляти треба першу ланку, на якій значення перестає відповідати
відредагованому primary target. Заборонено компенсувати помилку випадковим
додатковим поворотом в importer або exporter.

## 21. Критерії завершення

Робота вважається завершеною лише якщо одночасно виконано:

- чистий імпорт будує правильну DayZ-позу;
- Build Blender IK не змінює цю позу;
- hand location редагується через control;
- elbow редагується через pole control;
- wrist rotation не повертає й не переносить helper-напрямну;
- Bake не змінює видиму позу;
- export/reimport відтворює позу;
- in-game результат збігається з Blender;
- підтверджені висновки записані в ground truth із числовими та візуальними
  доказами.
