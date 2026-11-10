# Labeled multi-lingual dataset for English, Tamil script, and Tanglish
# Classes: Low, Medium, High, Critical

DATASET = [
    # --- CRITICAL (Mass casualties, building collapses, explosions, trapped victims, major fires) ---
    ("Massive chemical plant explosion, entire building collapsed and at least 20 people trapped inside rubble", "Critical"),
    ("Major high-rise apartment fire, families trapped on 8th floor calling for help, thick black toxic smoke", "Critical"),
    ("Bridge collapsed during peak rush hour traffic, multiple cars plunged into deep water, immediate rescue needed", "Critical"),
    ("Gas tanker explosion on main expressway, massive fireball engulfed passing buses, severe burns and casualties", "Critical"),
    ("Four story residential complex collapsed completely, loud screams from under concrete slabs, send search teams", "Critical"),
    ("Severe flash flood breached dam wall, village submerged underwater, children stranded on rooftops", "Critical"),
    ("Train derailment near station, three carriages overturned, multiple fatalities and critical injuries", "Critical"),
    ("Industrial boiler blast, building structure caved in, workers burning and trapped under heavy iron", "Critical"),
    ("Severe multi-vehicle pileup with oil tanker leak caught fire, 15 people burned and unresponsive", "Critical"),
    ("Huge landslide swept away 5 houses into valley, people buried alive under mud", "Critical"),
    
    # Tamil Critical
    ("கட்டிடம் முழுமையாக இடிந்து விழுந்தது! பலர் இடிபாடுகளுக்குள் சிக்கியுள்ளனர், உடனே மீட்புப்படை தேவை", "Critical"),
    ("பெரிய தொழிற்சாலையில் வெடிவிபத்து, தீ மளமளவென பரவுகிறது, 10க்கும் மேற்பட்டோர் காயம்", "Critical"),
    ("மழை வெள்ளம் வீடுகளை மூழ்கடித்தது, மக்கள் கூரை மீது தஞ்சம், உடனடி படகு மீட்பு தேவை", "Critical"),
    ("ரயில் விபத்து, மூன்று பெட்டிகள் தடம் புரண்டன, பலர் படுகாயம் உயிருக்கு ஆபத்து", "Critical"),
    ("சிலிண்டர் வெடித்து அடுக்குமாடி குடியிருப்பு இடிந்தது, அலறல் சத்தம் கேட்கிறது காப்பாற்றுங்கள்", "Critical"),

    # Tanglish Critical
    ("Periya building collapse aagiduchu, ulla niraya peru maatikitanga, seekiram vanga", "Critical"),
    ("Factory la periya blast, fire romba spread aagudhu, 10 peruku mela serious injury", "Critical"),
    ("Bridge collapse aayi cars ellam thanni kulla vizhundhuruchu, emergency rescue venum", "Critical"),
    ("Lorry and bus face to face accident, neraiya peruku ratham, unconscious ah irukanga", "Critical"),
    ("Gas cylinder vedichu veedu full ah thee pidichiduchu, aalunga ulla maatikitanga", "Critical"),
    ("Periya vellam vandhu veedellam moolgiduchu, roof mela nikkuranga kapathunga", "Critical"),

    # --- HIGH (Severe accidents, active fires, serious single/multiple injuries, chest pains) ---
    ("Head on collision between car and bike, rider has fractured skull and severe bleeding on highway", "High"),
    ("Elderly patient experiencing severe chest pain, left arm numbness and difficulty breathing", "High"),
    ("Commercial kitchen fire spreading to roof, restaurant evacuated but gas cylinder nearby", "High"),
    ("Severe road accident, two passengers trapped in crushed car cabin with leg fractures", "High"),
    ("Construction worker fell from 3rd floor scaffolding, bleeding from ear and spine suspected injured", "High"),
    ("Sudden anaphylactic shock and throat swelling after bee sting, patient gasping for air", "High"),
    ("Electrical transformer burst in crowded market, sparks and small fire spreading to clothing shops", "High"),
    ("School bus collided with truck, 4 children injured and crying in pain, need ambulance immediately", "High"),

    # Tamil High
    ("இரு சக்கர வாகனம் மீது கார் மோதி விபத்து, தலையில் பலத்த காயம் ரத்தம் கொட்டுகிறது", "High"),
    ("முதியவருக்கு மாரடைப்பு நெஞ்சு வலி, மூச்சு விட மிகவும் சிரமப்படுகிறார்", "High"),
    ("ஹோட்டல் சமையலறையில் திடீர் தீ விபத்து, அருகிலிருக்கும் கடைகளுக்கு பரவும் அபாயம்", "High"),
    ("கட்டுமான பணியாளர் மாடியிலிருந்து கீழே விழுந்து பலத்த காயம், அவசர ஆம்புலன்ஸ் தேவை", "High"),

    # Tanglish High
    ("Car and bike head-on crash, rider ku thalaila bayangarama bleeding ambulance venum", "High"),
    ("Thatha ku nenju vali vanthuruchu, moochu vida kashtapadraaru seekiram ambulance", "High"),
    ("Hotel la fire aagiduchu, pakathu kadai ku spread aagudhu fire engine anupunga", "High"),
    ("Kozhandhai ku seizure fits vandhiruchu, moochu ninnu pochudhu kapathunga", "High"),
    ("Transformer blast aagi street full ah sparks and fire, police and fire team venum", "High"),

    # --- MEDIUM (Moderate injuries, localized hazards, waterlogging without immediate drowning) ---
    ("Two wheeler skid on wet road, rider has painful shoulder dislocation and deep cuts", "Medium"),
    ("Localized water logging on street up to knee level, traffic stalled and two cars broken down", "Medium"),
    ("Small garbage dump fire behind residential layout, smoke irritating residents but contained", "Medium"),
    ("Kitchen burner flash burn on forearm, skin blistering, conscious and talking", "Medium"),
    ("Minor collision between two cars, fender bent, passengers shaken with minor bruises", "Medium"),
    ("Tree branch fell on parked car and electric cable, cable sparking on the road", "Medium"),
    ("Patient with high fever and sudden fainting episode, now conscious but very weak", "Medium"),

    # Tamil Medium
    ("சாலையில் வழுக்கி விழுந்ததில் தோள்பட்டை முறிவு மற்றும் சிராய்ப்பு காயங்கள்", "Medium"),
    ("தெருவில் முழங்கால் அளவு தண்ணீர் தேங்கி போக்குவரத்து தடைபட்டுள்ளது", "Medium"),
    ("குப்பை கிடங்கில் தீ பற்றி புகை மண்டலமாக உள்ளது", "Medium"),
    ("மரக்கிளை முறிந்து மின்கம்பி மீது விழுந்து தீப்பொறி பறக்கிறது", "Medium"),

    # Tanglish Medium
    ("Bike skid aagi vizhundhutaru, kai fracture aana maadhiri theriyudhu", "Medium"),
    ("Road la water logging, knee deep water vandhuruchu traffic jam", "Medium"),
    ("Kuppai thotila fire pudichirukku, smoke romba varudhu but controlled ah iruku", "Medium"),
    ("Maram kizhe vizhundhu wire cut aagiduchu, spark varudhu", "Medium"),
    ("Fever vandhu faint aayitaaru, ipo conscious ah irukaru but weak", "Medium"),

    # --- LOW (Minor scrapes, non-emergency inquiries, mild animal nuisance, small trash) ---
    ("Minor bicycle fall, slight scratch on knee, asking for nearby dispensary address", "Low"),
    ("Stray dog barking aggressively near society gate, no one bitten", "Low"),
    ("Street light blinking and buzzing sound in lane 4", "Low"),
    ("Cat stuck on boundary wall roof, meowing for help", "Low"),
    ("Small oil puddle on parking floor, need sand to cover", "Low"),
    ("Water leakage from roadside pipe, slight puddle on pavement", "Low"),

    # Tamil Low
    ("சைக்கிளிலிருந்து கீழே விழுந்து முட்டியில் லேசான சிராய்ப்பு", "Low"),
    ("தெரு நாய் குரைத்து பயமுறுத்துகிறது, கடிக்கவில்லை", "Low"),
    ("குடிநீர் குழாயில் சிறிய கசிவு ஏற்பட்டுள்ளது", "Low"),

    # Tanglish Low
    ("Cycle la irundhu vizhundhutan, kaal la chinna scratch avlothan", "Low"),
    ("Street light fuse poiruchu, night time darkness ah irukku", "Low"),
    ("Poonai wall mela maatikuchu irangu mudila", "Low"),
    ("Pipe leak aagi water waste aagudhu panchayat ku inform pananum", "Low"),
]
