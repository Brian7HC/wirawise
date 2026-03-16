#!/usr/bin/env python3
"""
Add comprehensive coffee Q&A pairs to knowledge base
"""

import json

# New comprehensive coffee Q&A pairs to add
new_qa_pairs = [
    # PRICING/MARKET - 6 pairs
    {
        "question_en": "What is the current coffee price?",
        "question_ki": "Bei ya kahūa nĩ īrīkū rĩu?",
        "answer_en": "Coffee prices in Kenya vary by grade at the Nairobi Coffee Exchange:\n\n**AA Grade:** KES 800-1,200 per kg\n**AB Grade:** KES 600-900 per kg\n**PB Grade:** KES 500-800 per kg\n\nFarmers receive approximately 60-80% of auction price after deductions. Prices change weekly! Check the NCE website or your cooperative for current rates.",
        "answer_ki": "Bei ya kahūa Kenya ĩringana na grade ya Nairobi Coffee Exchange:\n\n**Grade AA:** KES 800-1,200 kĩlo-inĩ\n**Grade AB:** KES 600-900 kĩlo-inĩ\n**Grade PB:** KES 500-800 kĩlo-inĩ\n\nArĩmi mahewaga 60-80% ya bei ya auction thutha wa mĩrĩto. Bei ĩcenjagio o wiki! Thugunda NCE kana cooperative yaku."
    },
    {
        "question_en": "How much is coffee per kilo?",
        "question_ki": "Kahūa kagũrũo shillingi cigana kĩlo-inĩ?",
        "answer_en": "Current coffee prices per kilo:\n\n- AA grade: KES 800-1,200\n- AB grade: KES 600-900\n- PB grade: KES 500-800\n- C grade: KES 400-600\n\nPrices fluctuate weekly based on auction. Your final payment depends on your cooperative's deductions for processing and marketing.",
        "answer_ki": "Bei ya kahūa kĩlo-inĩ rĩu:\n\n- Grade AA: KES 800-1,200\n- Grade AB: KES 600-900\n- Grade PB: KES 500-800\n- Grade C: KES 400-600\n\nBei ĩcenjagio o wiki o Nairobi Coffee Exchange. Mũrĩhwo waku ũringana na mĩrĩto ya cooperative."
    },
    {
        "question_en": "Where can I sell my coffee?",
        "question_ki": "Nĩ kambuni iriku ingiendia kahūa kakwa?",
        "answer_en": "You can sell coffee at:\n\n1. **Factory/Cooperative** - Most common, delivers cherries or parchment\n2. **Nairobi Coffee Exchange** - Auction through your factory\n3. **Direct to traders** - Less common, may get lower prices\n\nBest option: Join a reputable cooperative or factory that has good payment records.",
        "answer_ki": "Ungũrīsĩa kahūa:\n\n1. **Factory/Cooperative** - Ya mũno, owatara mbegũ kana parchment\n2. **Nairobi Coffee Exchange** - Auction through factory yaku\n3. **Direct kũrĩa traders** - Ĩtarĩ ya mũno, bei ĩrĩ ĩguhi\n\nNjega: Ingĩra cooperative kana factory ĩrĩ njega."
    },
    {
        "question_en": "What is the price for AA grade coffee?",
        "question_ki": "Bei ya grade AA ya kahūa nĩ īrīkū?",
        "answer_en": "AA grade coffee currently fetches KES 800-1,200 per kg at auction. This is the highest grade and gets premium prices.\n\nTo achieve AA grade:\n- Pick only fully ripe red cherries\n- Process carefully\n- Dry properly to 10-12% moisture\n- Store in good conditions",
        "answer_ki": "Grade AA ya kahūa ĩrĩhwo KES 800-1,200 kĩlo-inĩ o auction. Nĩ grade ĩrĩ igũrũ mũno.\n\nKũngĩona AA:\n- Tua tu mbegũ njirũ\n- Gũthondeka carefully\n- Ũmithia wega (10-12% moisture)\n- Ĩga conditions njega"
    },
    {
        "question_en": "Which factory pays best?",
        "question_ki": "Factory īrīkū īhūra wega?",
        "answer_en": "Factory payments vary based on:\n- Quality of cherries delivered\n- Processing standards\n- Auction prices that week\n- Cooperative deductions\n\nResearch factories in your area, ask other farmers about their payments, and consider joining one with good reputation and transparent pricing.",
        "answer_ki": "Mĩrĩhwo ya factory ĩringana na:\n- Mũcamo wa mbegũ\n- Standards ya processing\n- Bei ya auction\n- Mĩrĩto ya cooperative\n\nThugunda factories harĩa, ũria arĩmi mangĩ maheo, na ũrie ĩrĩa ĩrĩ njega."
    },
    {
        "question_en": "When do coffee factories pay farmers?",
        "question_ki": "Nĩ rĩ gāka factories marĩhwo arĩmi?",
        "answer_en": "Coffee factories typically pay:\n- **Advance payment** - When you deliver cherries (KES 20-40 per kg)\n- **Final payment** - After auction sale (2-4 weeks later)\n- **Bonus** - End of season if profits allow\n\nPayment timing varies by factory. Ask your cooperative about their payment schedule.",
        "answer_ki": "Factories marĩhwo:\n- **Mũrĩhwo wa mbere** - Rĩrĩa owatara mbegũ (KES 20-40 kĩlo-inĩ)\n- **Mũrĩhwo wa mũthia** - Thutha wa auction (wiki 2-4)\n- **Bonus** - End ya season\n\nŨria factory yaku ĩhe o ũteithio."
    },
    
    # WEATHER/CLIMATE - 4 pairs
    {
        "question_en": "When will rain come?",
        "question_ki": "Mbura ĩgũũka rĩ?",
        "answer_en": "Kenya has two main rain seasons:\n\n**Long Rains (March-May):** Main planting season\n**Short Rains (October-December):** Important for coffee\n\nCheck weather forecasts from Kenya Meteorological Department or listen to local radio for seasonal predictions.",
        "answer_ki": "Kenya ĩrĩ na mbura mĩrĩ 2:\n\n**Mbura nene (March-May):** Season ya kũhanda\n**Mbura njugu (October-December):** Ya kwiyũkia kahūa\n\nThugunda weather forecast kana radio."
    },
    {
        "question_en": "How do I protect coffee during drought?",
        "question_ki": "Nĩ ngĩkīra kahūa atĩa rĩrĩa kũrĩ kĩhũhũ?",
        "answer_en": "During drought:\n\n1. **Mulch heavily** - 10-15cm organic mulch around trees\n2. **Water deeply** - If irrigation available, water deeply but infrequently\n3. **Prune less** - Leave more foliage for shade\n4. **Control weeds** - Reduce competition for water\n5. **Apply foliar fertilizer** - Helps trees withstand stress\n\nDrought affects yields but healthy trees recover faster.",
        "answer_ki": "Rĩrĩa kĩhũhũ:\n\n1. **Ĩkĩra mũceng'i** - cm 10-15\n2. **Itĩrĩria maaĩ maingi** - kana ĩrĩ irrigation\n3. **Ceha mũnini** - Rĩka honge\n4. **Ruta ria** - Reduce competition\n5. **Ĩkĩra foliar** - Ĩteithĩaga mũtĩ"
    },
    {
        "question_en": "What to do during dry season?",
        "question_ki": "Nĩ ngĩka atĩa hĩndĩ ya kĩhũhũ?",
        "answer_en": "Dry season coffee care:\n\n1. **Mulch** - Maintain thick mulch layer\n2. **Irrigate** - Water deeply once a week if possible\n3. **Weed control** - Remove weeds that compete for water\n4. **Prune strategically** - Maintain balanced canopy\n5. **Monitor for stress** - Watch for wilting leaves\n\nConsider drought-resistant varieties like K7 for low rainfall areas.",
        "answer_ki": "Hĩndĩ ya kĩhũhũ:\n\n1. **Mũceng'i** - Ĩga mulch nene\n2. **Irrigate** - Itĩrĩria maaĩ o wiki\n3. **Ruta ria** - Ruta magĩa\n4. **Ceha** - Maintain canopy\n5. **Rora** - Rora mathangũ\n\nThuura K7 rĩrĩa mbura ĩtarĩ nyingĩ."
    },
    {
        "question_en": "How to irrigate coffee?",
        "question_ki": "Nĩ ngĩīra kahūa atĩa maaĩ?",
        "answer_en": "Coffee irrigation methods:\n\n1. **Drip irrigation** - Most efficient, delivers water to roots\n2. **Basin irrigation** - Dig basins around trees, fill with water\n3. **Sprinkler** - Can cover large areas\n\nWater requirements:\n- Young trees: 5-10 liters per week\n- Mature trees: 20-40 liters per week during dry spells\n\nBest time: Early morning or evening to reduce evaporation.",
        "answer_ki": "Njĩra za kũheya maaĩ kahūa:\n\n1. **Drip irrigation** - Ya mũno, heya maaĩ mĩri-inĩ\n2. **Basin** - Dig basins, jaza maaĩ\n3. **Sprinkler** - Cover area nyingĩ\n\nMaaĩ:\n- Mĩtĩ mĩnini: 5-10 liters o wiki\n- Mĩtĩ mĩkũrũ: 20-40 liters o wiki\n\nNjega: Rũciinĩ kana hwainĩ."
    },
    
    # PEST IDENTIFICATION - 5 pairs
    {
        "question_en": "What pest is this on my coffee?",
        "question_ki": "Tũtambi tũũ nĩ tũrĩkũ kahūa kwĩa?",
        "answer_en": "Common coffee pests in Kenya:\n\n1. **Antestia (Antestiopsis spp.)** - Small brown bugs, suck sap from berries and leaves\n2. **Coffee Berry Borer (Hypothenemus hampei)** - Small beetle that drills into berries\n3. **Coffee Stem Borer** - Larvae that tunnel into stems\n4. **Leaf Miners** - Create tunnels in leaves\n5. **Aphids** - Small insects on young shoots\n\nTake photos and consult your extension officer for exact identification.",
        "answer_ki": "Tũtambi twa kahūa Kenya:\n\n1. **Antestia** - Tũtambi tũnini brown, ciranwa mae na mathangũ\n2. **Berry Borer** - Tũtambi tũnini twĩra mbegũ-inĩ\n3. **Stem Borer** - Larvae twĩra gĩtina-inĩ\n4. **Leaf Miners** - Tũra tunnels mathangũ-inĩ\n5. **Aphids** - Tũtambi tũnini honge cia mbere\n\nKua photos, ũria extension officer."
    },
    {
        "question_en": "How to kill antestia bugs?",
        "question_ki": "Nĩ ngĩũraga atĩa antestia?",
        "answer_en": "Controlling Antestia:\n\n1. **Cultural:**\n   - Prune regularly for good air circulation\n   - Remove and destroy infected berries\n   - Keep farm clean\n\n2. **Chemical:**\n   - Spray pyrethroids (e.g., Cyclo 50EC)\n   - Mix 10ml per liter water\n   - Spray every 2-3 weeks during fruiting\n\n3. **Biological:**\n   - Encourage natural predators\n   - Some farmers use neem extract\n\nTiming: Start spraying when berries are developing.",
        "answer_ki": "Kũrūaia Antestia:\n\n1. **Cultural:**\n   - Ceha nĩguo rũhuho rũhĩtũke\n   - Ruta mbegũ irwarũ\n   - Gĩra mũgũnda itheru\n\n2. **Chemical:**\n   - Spray pyrethroids\n   - Tũkania 10ml per liter\n   - Spray o wiki 2-3\n\n3. **Biological:**\n   - Teithia predators\n   - Neem extract"
    },
    {
        "question_en": "My berries have holes - what is eating them?",
        "question_ki": "Mbegũ ciakwa ciarĩ na marima - nĩ tũtambi twĩa?",
        "answer_en": "Holes in coffee berries are usually caused by:\n\n1. **Coffee Berry Borer (CBB)** - Small holes, berries may fall prematurely\n2. **Birds** - Larger holes, often partial feeding\n3. **Antestia** - Multiple small punctures\n\n**If small holes inside berries:** Likely Berry Borer - pick all affected berries and destroy them. Spray with appropriate insecticide.",
        "answer_ki": "Marima mbegũ-inĩ gũtũmagwo nĩ:\n\n1. **Berry Borer** - Marima mĩnini, mbegũ ĩragũa\n2. **Ndege** - Marima nene\n3. **Antestia** - Punctures nyingĩ\n\n**Berry Borer:** Tua mbegũ irwarũ, cina. Spray insecticide."
    },
    {
        "question_en": "Small insects on my leaves",
        "question_ki": "Tũtambi tũnini mathangũ makwa",
        "answer_en": "Small insects on coffee leaves could be:\n\n1. **Aphids** - Small green/black insects on young shoots\n2. **Scale insects** - Small, immobile, on stems and leaves\n3. **Spider mites** - Very small, cause stippling\n4. **Mealybugs** - White, cottony masses\n\nTreatment depends on the insect. Take clear photos and consult your extension officer.",
        "answer_ki": "Tũtambi tũnini mathangũ-inĩ nĩ:\n\n1. **Aphids** - Tũnini green/black honge cia mbere\n2. **Scale** - Tũnini, ĩtarĩ mobile, gĩtina na mathangũ\n3. **Spider mites** - Nini mũno, tũma stippling\n4. **Mealybugs** - White, cottony\n\nTreatment ĩringana na tũtambi. Kua photos."
    },
    {
        "question_en": "What is eating my coffee leaves?",
        "question_ki": "Nĩ kĩĩ kĩrĩa kiragĩa mathangũ ma kahūa?",
        "answer_en": "Common causes of leaf damage:\n\n1. **Caterpillars** - Chew holes in leaves\n2. **Snails/Slugs** - Eat leaf edges\n3. **Leaf miners** - Create serpentine tunnels\n4. **Nutrient deficiency** - Yellowing, not insect damage\n5. **Disease** - Spots, discoloration\n\nInspect carefully - are there insects present? Are the holes irregular (caterpillars) or tunnels (miners)?",
        "answer_ki": "Ũrĩa wa mathangũ kũgarũka:\n\n1. **Caterpillars** - Tũra marima mathangũ-inĩ\n2. **Snails/Slugs** - Tũra matagĩ ya mathangũ\n3. **Leaf miners** - Tũra tunnels\n4. **Kũaga irio** - Yellowing\n5. **Mũrimũ** - Spots\n\nRora - kũrĩ tũtambi? Marima marĩ irregular?"
    },
    
    # FERTILIZER SPECIFIC - 5 pairs
    {
        "question_en": "How to apply NPK fertilizer?",
        "question_ki": "Nĩ ngĩhũthĩra NPK atĩa?",
        "answer_en": "NPK Application for Coffee:\n\n**Young trees (1-3 years):**\n- Year 1: 100g NPK per tree (split 2x)\n- Year 2: 200g NPK per tree (split 2x)\n- Year 3: 300g NPK per tree (split 2x)\n\n**Mature trees (4+ years):**\n- 400-600g NPK per tree per year\n- Split into 2 applications:\n  - First: At long rains start (March)\n  - Second: At short rains start (October)\n\n**How to apply:**\n1. Clear weeds around tree\n2. Spread in ring 30-60cm from stem\n3. Lightly cover with soil\n4. Apply when soil is moist",
        "answer_ki": "Kwĩkĩra NPK kahūa:\n\n**Mĩtĩ mĩnini (1-3 mĩaka):**\n- Mwaka 1: 100g (mĩrĩ 2)\n- Mwaka 2: 200g (mĩrĩ 2)\n- Mwaka 3: 300g (mĩrĩ 2)\n\n**Mĩtĩ mĩkũrũ (4+ mĩaka):**\n- 400-600g o mũtĩ o mwaka\n- Gaya mĩrĩ 2:\n  - Ya mbere: March\n  - Ya keerĩ: October\n\n**Kũhũthĩra:**\n1. Ruta ria\n2. Mwĩrĩra 30-60cm kuuma gĩtina-inĩ\n3. Humbĩra tĩĩri\n4. Apply rĩrĩa tĩĩri ũrĩ ũigũkũ"
    },
    {
        "question_en": "CAN or NPK - which is better for coffee?",
        "question_ki": "CAN kana NPK - nĩ īrīkū mwega kahūa?",
        "answer_en": "Both are important for coffee:\n\n**NPK (like 17:17:17):**\n- Contains Nitrogen, Phosphorus, Potassium\n- Use as primary fertilizer\n- Apply at start of rains (March, October)\n\n**CAN (Calcium Ammonium Nitrate):**\n- Mainly Nitrogen + Calcium\n- Use as top-up during growing season\n- Apply 6-8 weeks after NPK\n\n**Best practice:** Use both! NPK for base feeding, CAN for supplemental nitrogen during active growth.",
        "answer_ki": "Ziūsī ziwiri zĩ重要的 kahūa:\n\n**NPK:**\n- Ĩrĩ na Nitrogen, Phosphorus, Potassium\n- Primary fertilizer\n- Apply rĩrĩa mbura ĩkambĩrĩria\n\n**CAN:**\n- Nitrogen + Calcium mainly\n- Top-up hĩndĩ ya kũkũra\n- Apply wiki 6-8 thutha wa NPK\n\n**Njega:** Use both! NPK kũria base, CAN kũria supplement."
    },
    {
        "question_en": "When to apply fertilizer to coffee?",
        "question_ki": "Nĩ hĩndĩ īrīkū ya kwĩkĩra kahūa mboleo?",
        "answer_en": "Best fertilizer timing for coffee:\n\n**First Application: March-April (Long Rains)**\n- Apply NPK 17:17:17\n- Soil is moist - fertilizer dissolves well\n- Apply 50-60% of annual dose\n\n**Second Application: September-October (Short Rains)**\n- Apply remaining NPK\n- Before or just after rains start\n- Apply 40-50% of annual dose\n\n**Top Dressing:**\n- CAN 6-8 weeks after each NPK\n\n❌ Never apply when soil is dry or heavy rain expected.",
        "answer_ki": "Hĩndĩ njega ya kwĩkĩra mboleo kahūa:\n\n**Kwĩkĩra kwa Mbere: March-April**\n- Apply NPK\n- Tĩĩri ũrĩ ũigũkũ\n- 50-60% ya mwaka\n\n**Kwĩkĩra kwa Keerĩ: September-October**\n- Apply NPK ĩrĩa ĩtigarĩte\n- 40-50% ya mwaka\n\n**Top Dressing:**\n- CAN wiki 6-8 thutha wa NPK"
    },
    {
        "question_en": "How much fertilizer per coffee tree?",
        "question_ki": "Mboleo ĩigana atĩa o mũtĩ ũmwe wa kahūa?",
        "answer_en": "Fertilizer rates per coffee tree:\n\n**Mature trees (4+ years):**\n- NPK 17:17:17: 400-600g per tree per year\n- CAN: 200g per tree per year\n\n**Young trees:**\n- Year 1: 100g NPK\n- Year 2: 200g NPK  \n- Year 3: 300g NPK\n\nSplit applications: Apply half in March, half in October.",
        "answer_ki": "Mboleo o mũtĩ ũmwe wa kahūa:\n\n**Mĩtĩ mĩkũrũ:**\n- NPK: 400-600g\n- CAN: 200g\n\n**Mĩtĩ mĩnini:**\n- Mwaka 1: 100g NPK\n- Mwaka 2: 200g NPK\n- Mwaka 3: 300g NPK\n\nGaya: Half March, half October."
    },
    {
        "question_en": "Is foliar fertilizer necessary for coffee?",
        "question_ki": "Mboleo ya foliar nĩ ya bata kahūa?",
        "answer_en": "Foliar fertilizer is optional but beneficial:\n\n**Benefits:**\n- Quick nutrient absorption\n- Addresses micronutrient deficiencies\n- Helpful during stress periods\n\n**When to apply:**\n- At flowering (boron is critical)\n- During berry development\n- When leaves show deficiency signs\n\n**Recommended:**\n- Boron + Zinc foliar spray\n- Apply every 4-6 weeks during growing season\n\nIt's not required but can significantly improve yields.",
        "answer_ki": "Foliar fertilizer nĩ optional no ĩhotaga:\n\n**Benefits:**\n- Quick absorption\n- Addresses micronutrients\n- Helpful stress-inĩ\n\n**Hĩndĩ:**\n- Hĩndĩ ya mahũa (boron critical)\n- Mbegũ cĩkũkũra\n- Mathangũ maonanĩria deficiency\n\n**Recommended:**\n- Boron + Zinc spray\n- Apply o wiki 4-6"
    },
    
    # COSTS - 4 pairs
    {
        "question_en": "How much does coffee farming cost?",
        "question_ki": "Kũrĩma kahūa kũrĩhĩthagia pesa cigana?",
        "answer_en": "Coffee farming costs per acre per year:\n\n**Inputs:**\n- Fertilizer: KES 15,000-20,000\n- Fungicides: KES 5,000-10,000\n- Labor (pruning, harvesting): KES 20,000-30,000\n- Transport: KES 5,000-10,000\n\n**Total: KES 45,000-70,000 per acre per year**\n\nReturns depend on yields and prices. Well-managed acre can produce 300-500kg, worth KES 200,000-500,000.",
        "answer_ki": "Mĩgĩrĩrĩro ya kũrĩma kahūa acre-inĩ o mwaka:\n\n**Mĩhĩra:**\n- Mboleo: KES 15,000-20,000\n- Fungicides: KES 5,000-10,000\n- Labor: KES 20,000-30,000\n- Transport: KES 5,000-10,000\n\n**Total: KES 45,000-70,000 acre-inĩ o mwaka**\n\nMĩrĩho ĩringana na yield na bei. Acre ĩrĩa ĩkorwo njega ĩhotaga 300-500kg, ya KES 200,000-500,000."
    },
    {
        "question_en": "What is the cost of CBD spray?",
        "question_ki": "Bei ya dawa ya CBD nĩ īrīkū?",
        "answer_en": "CBD (Coffee Berry Disease) spray costs:\n\n**Copper-based fungicide:**\n- 50g pack: KES 300-500\n- Mix with 20 liters water\n- Apply 5-7 times per season\n\n**Cost per acre:** KES 5,000-10,000 per season\n\n**Important:** Start spraying at 40% flowering and continue until berries harden.",
        "answer_ki": "Bei ya CBD spray:\n\n**Copper fungicide:**\n- 50g: KES 300-500\n- Tũkania maaĩ 20 liters\n- Apply 5-7 times per season\n\n**Cost per acre:** KES 5,000-10,000 per season"
    },
    {
        "question_en": "Where to buy cheap coffee seedlings?",
        "question_ki": "Nĩ mūthĩ ūrīkū ndĩgũre mĩūngūrũa ya kahūa bei ĩguhi?",
        "answer_en": "Where to buy coffee seedlings:\n\n**Best sources:**\n1. Coffee Research Institute (CRI) Ruiru - Certified, KES 50-60 each\n2. County Government nurseries - Sometimes subsidized\n3. Licensed private nurseries with KEPHIS certification\n\n⚠️ Avoid roadside vendors - many sell fake Ruiru 11!\n\n**What to look for:**\n- Height 30-40cm\n- 1-2 pairs of branches\n- Healthy green leaves\n- Hardened (not fresh from shade)",
        "answer_ki": "Harĩa wa kũgũra mĩũngũrũa:\n\n**Nzega:**\n1. CRI Ruiru - Certified, KES 50-60\n2. County nurseries - Subsidized\n3. Private nurseries licensed\n\n⚠️ Nyĩhĩra vendors njĩra-inĩ!\n\n**Rĩa wa kũrora:**\n- Height 30-40cm\n- Honge 1-2\n- Mathangũ mega"
    },
    {
        "question_en": "Cost per acre for coffee farming?",
        "question_ki": "Mĩgĩrĩrĩro ya acre ya kahūa nĩ īrīkū?",
        "answer_en": "Cost breakdown per acre per year:\n\n**Year 1 (Establishment):**\n- Seedlings (1,000): KES 50,000-60,000\n- Planting: KES 10,000\n- First fertilizer: KES 15,000\n- Total: KES 75,000-85,000\n\n**Years 2+ (Maintenance):**\n- Fertilizer: KES 20,000-25,000\n- Pesticides: KES 10,000-15,000\n- Labor: KES 30,000-40,000\n- Transport & misc: KES 10,000\n- Total: KES 70,000-90,000/year",
        "answer_ki": "Mĩgĩrĩrĩro acre-inĩ o mwaka:\n\n**Mwaka 1:**\n- Mĩũngũrũa: KES 50,000-60,000\n- Kũhanda: KES 10,000\n- Mboleo: KES 15,000\n- Total: KES 75,000-85,000\n\n**Mĩaka 2+:**\n- Mboleo: KES 20,000-25,000\n- Pesticides: KES 10,000-15,000\n- Labor: KES 30,000-40,000\n- Total: KES 70,000-90,000/year"
    },
    
    # PROCESSING/QUALITY - 4 pairs
    {
        "question_en": "How to process coffee for best price?",
        "question_ki": "Nĩ ndĩthondeke atĩa kahūa nĩguo ngĩe bei nene?",
        "answer_en": "Processing for best price:\n\n1. **Harvest correctly:**\n   - Pick ONLY ripe red cherries\n   - No green or overripe berries\n\n2. **Deliver same day:**\n   - Within 6 hours of picking\n   - Keep cherries cool\n\n3. **Processing method:**\n   - Wet processing (washed) gets better prices\n   - Proper fermentation (12-36 hours)\n   - Thorough washing\n\n4. **Drying:**\n   - Dry to 10-12% moisture\n   - Even drying, avoid direct sun\n   - Protect from rain",
        "answer_ki": "Gũthondeka kũngĩona bei nene:\n\n1. **Getha correctly:**\n   - Tua tu mbegũ njirũ\n   - No green or overripe\n\n2. **Twara same day:**\n   - Thutha wa mathaa 6\n   - Rĩka mbegũ ĩhehu\n\n3. **Method:**\n   - Wet processing (washed)\n   - Fermentation (12-36 hours)\n   - Wash thoroughly\n\n4. **Ũmithia:**\n   - To 10-12% moisture\n   - Even drying"
    },
    {
        "question_en": "How to achieve AA grade?",
        "question_ki": "Nĩ ndĩreke atĩa kahūa kakorwo grade AA?",
        "answer_en": "Steps to AA grade:\n\n1. **Start with good variety:** SL28, SL34\n2. **Harvest only ripe:** No green, no overripe\n3. **Deliver same day:** Within 6 hours\n4. **Process properly:**\n   - Pulp immediately\n   - Ferment 12-36 hours\n   - Wash completely\n5. **Dry correctly:**\n   - 10-12% moisture\n   - Even drying\n6. **Store properly:**\n   - Cool, dry place\n   - On pallets\n   - Away from odors",
        "answer_ki": "Njĩra za AA grade:\n\n1. **Mũthemba mwega:** SL28, SL34\n2. **Tua njirũ:** No green, no overripe\n3. **Twara same day:** 6 hours\n4. **Process:**\n   - Pulp immediately\n   - Ferment 12-36 hours\n5. **Ũmithia:**\n   - 10-12% moisture\n6. **Store:**\n   - Cool, dry"
    },
    {
        "question_en": "Wet vs dry processing - which is better?",
        "question_ki": "Wet kana dry processing - nĩ īrīkū mwega?",
        "answer_en": "Processing methods comparison:\n\n**Wet (Washed) Processing:**\n- Better quality, higher prices\n- More labor intensive\n- Needs water access\n- Clean, bright cup\n- Fetches premium prices (AA, AB grades)\n\n**Dry (Natural) Processing:**\n- Simpler, less water needed\n- Lower quality typically\n- More fruity flavors\n- Lower prices\n\n**Recommendation:** Wet processing for better prices.",
        "answer_ki": "Njĩra ziganĩrio:\n\n**Wet (Washed):**\n- Mũcamo mwega, bei nene\n- Labor intensive\n- Needs water\n- Clean cup\n- Premium prices\n\n**Dry (Natural):**\n- Simple, less water\n- Lower quality\n- Fruity flavors\n- Lower prices\n\n**Recommendation:** Wet processing."
    },
    {
        "question_en": "How to dry coffee properly?",
        "question_ki": "Nĩ ngĩithie atĩa kahūa?",
        "answer_en": "Proper coffee drying:\n\n**Ideal moisture:** 10-12%\n\n**Methods:**\n1. **Raised beds** - Best, good airflow\n2. **Parabolic driers** - Good for rain protection\n3. **Concrete platforms** - Acceptable\n\n**Tips:**\n- Turn beans regularly (3-4x daily)\n- Dry in thin layers (2-5cm)\n- Protect from rain\n- Avoid direct hot sun (causes cracking)\n- Drying time: 7-14 days\n\n**Test:** Beans should feel hard and snap, not bend.",
        "answer_ki": "Kũithia kahūa:\n\n**Moisture:** 10-12%\n\n**Njĩra:**\n1. **Raised beds** - Njega, rũhuho\n2. **Parabolic** - Rain protection\n3. **Concrete** - OK\n\n**Tips:**\n- Turn 3-4x daily\n- Thin layers (2-5cm)\n- Protect from rain\n- Avoid hot sun\n- Time: 7-14 days"
    },
    
    # YOUNG TREES - 4 pairs
    {
        "question_en": "How to care for young coffee trees?",
        "question_ki": "Nĩ ngĩĩyũre atĩa mĩtĩ ya kahūa ĩrĩa ĩnini?",
        "answer_en": "Young coffee tree care:\n\n**Watering:**\n- 5-10 liters per week\n- More frequent in dry weather\n\n**Weeding:**\n- Keep 1m radius weed-free\n- Don't damage shallow roots\n\n**Fertilizer:**\n- Year 1: 100g NPK split 2x\n- Year 2: 200g NPK split 2x\n- Year 3: 300g NPK split 2x\n\n**Shade:**\n- Provide temporary shade\n- Remove gradually after 6 months\n\n**Pruning:**\n- Remove suckers regularly\n- Train single stem initially",
        "answer_ki": "Kũĩyũra mĩtĩ mĩnini:\n\n**Maaĩ:**\n- 5-10 liters o wiki\n\n**Weeding:**\n- Keep 1m radius itheru\n- Ndũkĩrute mĩri\n\n**Mboleo:**\n- Mwaka 1: 100g NPK\n- Mwaka 2: 200g NPK\n- Mwaka 3: 300g NPK\n\n**Kĩruru:**\n- Provide temporary\n- Remove after 6 months\n\n**Kũceha:**\n- Ruta suckers"
    },
    {
        "question_en": "How much water for coffee seedlings?",
        "question_ki": "Maaĩ maigana atĩa ma mĩūngūrũa ya kahūa?",
        "answer_en": "Water requirements for seedlings:\n\n**First month:**\n- Water daily or every other day\n- Keep soil consistently moist\n- 1-2 liters per seedling\n\n**Months 2-3:**\n- Water every 2-3 days\n- 2-3 liters per seedling\n\n**After establishment (3+ months):**\n- Water weekly\n- 5-10 liters per seedling\n\n**Signs of too much water:**\n- Yellowing leaves\n- Wilting despite wet soil\n- Root rot\n\n**Signs of too little water:**\n- Drooping leaves\n- Slow growth\n- Dry soil",
        "answer_ki": "Maaĩ ma mĩũngũrũa:\n\n**Mĩezi 1:**\n- Water daily\n- Keep soil moist\n- 1-2 liters\n\n**Mĩezi 2-3:**\n- Water o wiki 2-3\n- 2-3 liters\n\n**After 3 months:**\n- Water weekly\n- 5-10 liters"
    },
    {
        "question_en": "Why is my seedling dying?",
        "question_ki": "Nĩ kĩĩ gĩkũrĩa kĩūngūrũa kĩrĩa kĩagũa?",
        "answer_en": "Common causes of seedling death:\n\n1. **Overwatering** - Roots rot, leaves yellow\n2. **Underwatering** - Leaves droop, soil dry\n3. **Too much sun** - Leaves scorch\n4. **Disease** - CBB, damping-off fungus\n5. **Pests** - Termites, nematodes\n6. **Poor soil** - Wrong pH, compaction\n\n**What to check:**\n- Soil moisture level\n- Leaf color and spots\n- Stem at soil line\n- Root health\n\n**Solution:** Fix the cause immediately. Remove dead seedlings.",
        "answer_ki": "Ũrĩa wa kũgũa kwa mĩūngũrũa:\n\n1. **Too much water** - Mĩri ĩrabutha, mathangũ ma ngoikoni\n2. **Too little water** - Mathangũ maragũra, tĩĩri haũmũ\n3. **Sun too strong** - Mathangũ maũma\n4. **Disease** - CBB, fungus\n5. **Pests** - Termites\n\n**Check:**\n- Moisture\n- Leaf color\n- Stem\n- Roots"
    },
    {
        "question_en": "When does coffee start bearing fruit?",
        "question_ki": "Nĩ rĩ kahūa kambĩrĩĩria kũciara?",
        "answer_en": "Coffee bearing timeline:\n\n**Ruiru 11:**\n- First harvest: 18-24 months after planting\n- Full production: 3-4 years\n\n**Batian:**\n- First harvest: 24-30 months\n- Full production: 4-5 years\n\n**SL varieties:**\n- First harvest: 2-3 years\n- Full production: 4-5 years\n\n**Factors affecting:**\n- Altitude\n- Soil fertility\n- Rainfall\n- Tree care\n- Variety",
        "answer_ki": "Hĩndĩ ya kahūa kũciara:\n\n**Ruiru 11:**\n- Getha ya mbere: 18-24 months\n- Full production: 3-4 years\n\n**Batian:**\n- Getha ya mbere: 24-30 months\n- Full production: 4-5 years\n\n**SL varieties:**\n- Getha ya mbere: 2-3 years\n- Full production: 4-5 years"
    },
    
    # EMERGENCY - 5 pairs
    {
        "question_en": "All my coffee is dying - help!",
        "question_ki": "Kahūa yakwa yothe ĩrakua - nĩndeteithie!",
        "answer_en": "🚨 EMERGENCY - Coffee trees dying!\n\n**Quick diagnosis:**\n1. Check leaves: Yellow? Spots? Wilting?\n2. Check berries: Black spots? Dropping?\n3. Check stems: Holes? Bark peeling?\n4. Check roots: Brown/mushy?\n\n**Immediate actions:**\n1. Stop watering if soil waterlogged\n2. Remove heavily affected branches\n3. Spray copper fungicide as first aid\n4. Apply foliar fertilizer for stress relief\n5. Call extension officer TODAY\n\n⚠️ If >50% affected, this is an emergency!",
        "answer_ki": "🚨 HARAKA - Kahūa ĩrakua!\n\n**Thugunda:**\n1. Mathangũ: Yellow? Spots? Wilting?\n2. Mbegũ: Black spots? Dropping?\n3. Gĩtina: Holes?\n4. Mĩri: Brown?\n\n**Gwĩka o rĩu:**\n1. TIGA kũhe maaĩ\n2. Ruta honge irwarũ\n3. Haka copper fungicide\n4. Ĩkĩra foliar\n5. Hũũra extension officer"
    },
    {
        "question_en": "All leaves are falling off my coffee!",
        "question_ki": "Mathangũ mothe ma kahūa makwa marĩragũa!",
        "answer_en": "🚨 Leaf drop emergency!\n\n**Most likely causes:**\n1. **Coffee Leaf Rust (CLR)** - Orange spots underneath\n2. **Severe drought** - No rain for weeks\n3. **Root rot** - Overwatering, poor drainage\n4. **Chemical damage** - Herbicide drift\n\n**Immediate steps:**\n1. Check leaf undersides for orange powder\n2. Check soil moisture\n3. Spray copper fungicide IMMEDIATELY\n4. Apply thick mulch (10-15cm)\n5. If root rot, STOP watering, improve drainage\n\n**Recovery:** With treatment, trees can recover in 2-4 months if roots are healthy.",
        "answer_ki": "🚨 Mathangũ kũgũa!\n\n**Ũrĩa mũno:**\n1. **CLR** - Orange powder nthĩ\n2. **Drought** - No rain\n3. **Root rot** - Too much water\n4. **Chemical** - Herbicide\n\n**Steps:**\n1. Rora nthĩ ya mathangũ\n2. Thugunda moisture\n3. Haka copper o rĩu\n4. Ĩkĩra mulch 10-15cm"
    },
    {
        "question_en": "My coffee has black spots on berries!",
        "question_ki": "Kahūa kakwa karĩ na mathĩna mĩirũ mbegũ-inĩ!",
        "answer_en": "🚨 This is likely CBD (Coffee Berry Disease)!\n\n**CBD Symptoms:**\n- Dark, sunken spots on green berries\n- Berries turn black and mummify\n- Affects all berry sizes\n- Worst in wet, cool weather\n\n**Treatment - ACT NOW:**\n1. Pick ALL affected berries (black/mummified)\n2. Burn or bury them (don't compost!)\n3. Spray copper fungicide IMMEDIATELY\n4. Repeat spray every 2-3 weeks\n5. Start preventive program next season\n\n**Cost:** KES 500-800 per acre per spray",
        "answer_ki": "🚨 Ũyũ nĩ CBD!\n\n**Kĩmenyithĩrio:**\n- Mathĩna mĩirũ mbegũ-inĩ njĩrũrĩa\n- Mbegũ ĩcoka njirũ\n- Affects all sizes\n\n**Ũhonokio - GWĨKA O RĨU:**\n1. Tua mbegũ ciothe irwarũ\n2. Cina kana cithike\n3. Haka copper fungicide\n4. Repeat o wiki 2-3"
    },
    {
        "question_en": "Tree is wilting - what do I do?",
        "question_ki": "Mũtĩ ũrĩkũura - nĩ ndĩka atĩa?",
        "answer_en": "🚨 Wilting coffee tree!\n\n**Possible causes:**\n1. **Water stress** - Too little OR too much water\n2. **Root rot** - Fungal infection in roots\n3. **Stem borer** - Larvae in stem\n4. **Bacterial blight** - Disease\n5. **Drought** - Lack of water\n\n**Quick check:**\n- Feel soil - wet or dry?\n- Check stem for holes\n- Look at leaf undersides\n- Dig gently to check roots\n\n**Action:**\n1. Fix water issue first\n2. Spray preventive fungicide\n3. Call extension officer for diagnosis",
        "answer_ki": "🚨 Mũtĩ ũrĩkũura!\n\n**Ũrĩa possible:**\n1. **Water** - Too little OR too much\n2. **Root rot** - Fungus\n3. **Stem borer** - Larvae\n4. **Disease**\n\n**Check:**\n- Soil - wet or dry?\n- Stem for holes\n- Roots\n\n**Action:**\n1. Fix water\n2. Spray fungicide\n3. Call extension"
    },
    {
        "question_en": "Quick! My coffee needs help now!",
        "question_ki": "Haraka! Kahūa yangũ ĩbataraga ũteithio o rĩu!",
        "answer_en": "🚨 QUICK HELP NEEDED!\n\n**If berries have black spots:**\n→ Pick affected berries NOW\n→ Spray copper fungicide TODAY\n→ Repeat in 2 weeks\n\n**If leaves are falling:**\n→ Spray copper fungicide NOW\n→ Apply thick mulch\n→ Water if soil is dry\n\n**If tree is wilting:**\n→ Check soil moisture\n→ Fix water issue\n→ Spray preventive fungicide\n\n**General first aid:**\n1. Copper fungicide spray\n2. Foliar fertilizer\n3. Mulch around trees\n4. Call extension officer\n\nDon't wait - early action saves trees!",
        "answer_ki": "🚨 ŨTEITHIO WA HARAKA!\n\n**Mbegũ na mathĩna mĩirũ:**\n→ Tua mbegũ irwarũ O RĨU\n→ Haka copper TODAY\n→ Repeat o wiki 2\n\n**Mathangũ magũa:**\n→ Haka copper NOW\n→ Ĩkĩra mulch\n→ Water kana dry\n\n**Mũtĩ ũkũura:**\n→ Check moisture\n→ Fix water\n→ Spray fungicide"
    },
]

# Load existing KB
with open('data/knowledge/comprehensive_qa.json', 'r', encoding='utf-8') as f:
    kb = json.load(f)

# Find Coffee topic
coffee_topic = None
for topic in kb.get('topics', []):
    if topic.get('topic') == 'Coffee':
        coffee_topic = topic
        break

if coffee_topic:
    existing_count = len(coffee_topic.get('qa_pairs', []))
    coffee_topic['qa_pairs'].extend(new_qa_pairs)
    new_count = len(coffee_topic.get('qa_pairs', []))
    
    # Update metadata
    kb['metadata']['total_qa_pairs'] = sum(len(t.get('qa_pairs', [])) for t in kb.get('topics', []))
    kb['metadata']['last_updated'] = '2024'
    
    # Save
    with open('data/knowledge/comprehensive_qa.json', 'w', encoding='utf-8') as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Added {len(new_qa_pairs)} new Q&A pairs to Coffee topic")
    print(f"   Before: {existing_count} pairs")
    print(f"   After: {new_count} pairs")
    print(f"   Total KB: {kb['metadata']['total_qa_pairs']} pairs")
else:
    print("❌ Coffee topic not found!")
