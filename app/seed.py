from extensions import db
from app.models import (
    ServiceCategory, Service, PaymentMethod, Branch,
    HomepageSection, FAQ, SiteSetting, Page, EmailTemplate, Destination, Package
)


def seed_data():
    if ServiceCategory.query.first():
        print("Data already seeded.")
        return

    # --- Categories ---
    categories = [
        {
            "slug": "ticketing-transportation",
            "name_ne": "टिकटिङ र यातायात",
            "name_en": "Ticketing & Transportation",
            "description_ne": "घरेलु तथा अन्तर्राष्ट्रिय उडान, रेल, बस र केबलकार टिकट सेवा।",
            "description_en": "Domestic & international flights, railway, bus and cable car tickets.",
            "icon": "plane",
            "sort_order": 1,
        },
        {
            "slug": "visa-immigration",
            "name_ne": "भिसा र अध्यागमन",
            "name_en": "Visa & Immigration",
            "description_ne": "पर्यटक, व्यापार, विद्यार्थी भिसा सहायता र VFS अपोइन्टमेन्ट।",
            "description_en": "Tourist, business, student visa assistance and VFS appointments.",
            "icon": "passport",
            "sort_order": 2,
        },
        {
            "slug": "documentation-government",
            "name_ne": "कागजात र सरकारी सेवा",
            "name_en": "Documentation & Government Services",
            "description_ne": "पुलिस क्लियरेन्स, श्रम स्वीकृति, अनुवाद र नोटरी सेवा।",
            "description_en": "Police clearance, labour permit, translation and notary services.",
            "icon": "document",
            "sort_order": 3,
        },
        {
            "slug": "tours-hospitality",
            "name_ne": "टुर र आतिथ्य",
            "name_en": "Tours & Hospitality",
            "description_ne": "घरेलु तथा अन्तर्राष्ट्रिय टुर प्याकेज र होटल बुकिङ।",
            "description_en": "Domestic & international tour packages and hotel booking.",
            "icon": "map",
            "sort_order": 4,
        },
        {
            "slug": "insurance",
            "name_ne": "बीमा",
            "name_en": "Insurance",
            "description_ne": "यात्रा बीमा र सुरक्षा योजना परामर्श।",
            "description_en": "Travel insurance and protection consultation.",
            "icon": "shield",
            "sort_order": 5,
        },
        {
            "slug": "education",
            "name_ne": "शिक्षा परामर्श",
            "name_en": "Education Consultancy",
            "description_ne": "विदेश अध्ययन मार्गदर्शन र संस्थागत कागजात।",
            "description_en": "Study abroad guidance and institutional documentation.",
            "icon": "graduation",
            "sort_order": 6,
        },
        {
            "slug": "corporate-services",
            "name_ne": "कर्पोरेट सेवा",
            "name_en": "Corporate Services",
            "description_ne": "लेखा समर्थन, सफ्टवेयर तालिम र व्यापारिक कागजात।",
            "description_en": "Accounting support, software training and business documentation.",
            "icon": "briefcase",
            "sort_order": 7,
        },
    ]

    cat_map = {}
    for c in categories:
        cat = ServiceCategory(**c)
        db.session.add(cat)
        db.session.flush()
        cat_map[c["slug"]] = cat.id

    # Sample services
    services = [
        {
            "category_id": cat_map["ticketing-transportation"],
            "slug": "domestic-flights",
            "name_ne": "घरेलु उडान टिकट",
            "name_en": "Domestic Flight Tickets",
            "short_desc_ne": "नेपालभित्रका प्रमुख शहरहरूमा उडान टिकट।",
            "short_desc_en": "Flight tickets to major cities within Nepal.",
            "is_featured": True,
        },
        {
            "category_id": cat_map["ticketing-transportation"],
            "slug": "international-flights",
            "name_ne": "अन्तर्राष्ट्रिय उडान टिकट",
            "name_en": "International Flight Tickets",
            "short_desc_ne": "विश्वभरका गन्तव्यका लागि उडान टिकट।",
            "short_desc_en": "Flight tickets to destinations worldwide.",
            "is_featured": True,
        },
        {
            "category_id": cat_map["visa-immigration"],
            "slug": "tourist-visa",
            "name_ne": "पर्यटक भिसा सहायता",
            "name_en": "Tourist Visa Assistance",
            "short_desc_ne": "पर्यटक भिसा आवेदन र कागजात सहयोग।",
            "short_desc_en": "Tourist visa application and document support.",
            "description_ne": "पर्यटक भिसा आवेदन, VFS अपोइन्टमेन्ट र कागजात तयारीमा सहयोग।",
            "description_en": "Help with tourist visa application, VFS appointment and document preparation.",
            "requirements_ne": "• पासपोर्ट (६ महिना मान्य)\n• पासपोर्ट साइज फोटो\n• यात्रा योजना / होटल बुकिङ\n• बैंक स्टेटमेन्ट (माग अनुसार)",
            "requirements_en": "• Passport (valid 6+ months)\n• Passport-size photos\n• Travel plan / hotel booking\n• Bank statement (if required)",
            "requires_documents": True,
            "is_featured": True,
        },
        {
            "category_id": cat_map["documentation-government"],
            "slug": "police-clearance",
            "name_ne": "पुलिस क्लियरेन्स सहयोग",
            "name_en": "Police Clearance Assistance",
            "short_desc_ne": "पुलिस क्लियरेन्स रिपोर्ट प्राप्त गर्न सहयोग।",
            "short_desc_en": "Assistance for obtaining Police Clearance Report.",
            "description_ne": "हामीले तपाईंलाई पुलिस क्लियरेन्स रिपोर्ट (PCR) प्राप्त गर्न पूर्ण सहयोग गर्छौं।",
            "description_en": "Full assistance to obtain a Police Clearance Report (PCR).",
            "requirements_ne": "• पासपोर्टको कपी\n• नागरिकताको कपी\n• हालसालैको पासपोर्ट साइज फोटो\n• आवेदन फारम",
            "requirements_en": "• Passport copy\n• Citizenship copy\n• Recent passport-size photo\n• Application form",
            "requires_documents": True,
            "is_featured": True,
        },
        {
            "category_id": cat_map["documentation-government"],
            "slug": "shram-swikriti",
            "name_ne": "श्रम स्वीकृति सहयोग",
            "name_en": "Shram Swikriti Assistance",
            "short_desc_ne": "श्रम स्वीकृति प्रक्रियामा पूर्ण सहयोग।",
            "short_desc_en": "Full assistance for labour permit process.",
            "requirements_ne": "• पासपोर्ट\n• भिसा / रोजगार सम्झौता\n• मेडिकल रिपोर्ट\n• अन्य माग अनुसारका कागजात",
            "requirements_en": "• Passport\n• Visa / employment contract\n• Medical report\n• Other documents as required",
            "requires_documents": True,
        },

        {
            "category_id": cat_map["tours-hospitality"],
            "slug": "domestic-tours",
            "name_ne": "घरेलु टुर प्याकेज",
            "name_en": "Domestic Tour Packages",
            "short_desc_ne": "नेपालका लोकप्रिय गन्तव्यका टुर प्याकेज।",
            "short_desc_en": "Tour packages to popular destinations in Nepal.",
            "is_featured": True,
        },
        {
            "category_id": cat_map["insurance"],
            "slug": "travel-insurance",
            "name_ne": "यात्रा बीमा",
            "name_en": "Travel Insurance",
            "short_desc_ne": "यात्रा सुरक्षाका लागि बीमा योजना।",
            "short_desc_en": "Insurance plans for travel protection.",
        },
        {
            "category_id": cat_map["corporate-services"],
            "slug": "corporate-travel-desk",
            "name_ne": "कर्पोरेट ट्राभल डेस्क",
            "name_en": "Corporate Travel Desk",
            "short_desc_ne": "कम्पनी कर्मचारी यात्रा व्यवस्थापन।",
            "short_desc_en": "Employee travel management for companies.",
            "description_ne": "कर्पोरेट टिमका लागि उडान, होटल र यात्रा योजना।",
            "description_en": "Flights, hotels and travel planning for corporate teams.",
            "is_featured": True,
            "is_published": True,
        },
        {
            "category_id": cat_map["corporate-services"],
            "slug": "business-visa-support",
            "name_ne": "व्यापारिक भिसा सहयोग",
            "name_en": "Business Visa Support",
            "short_desc_ne": "व्यापारिक भ्रमणका लागि भिसा सहायता।",
            "short_desc_en": "Visa assistance for business travel.",
            "requires_documents": True,
            "is_published": True,
        },
        {
            "category_id": cat_map["corporate-services"],
            "slug": "corporate-accounts",
            "name_ne": "कर्पोरेट खाता / बिलिङ",
            "name_en": "Corporate Accounts & Billing",
            "short_desc_ne": "मासिक बिलिङ र कम्पनी खाता व्यवस्थापन।",
            "short_desc_en": "Monthly billing and company account management.",
            "is_published": True,
        },
        {
            "category_id": cat_map["corporate-services"],
            "slug": "group-bookings",
            "name_ne": "समूह बुकिङ",
            "name_en": "Group Bookings",
            "short_desc_ne": "ठूलो समूहका लागि टिकट र प्याकेज।",
            "short_desc_en": "Tickets and packages for large groups.",
            "is_published": True,
        },

        {
            "category_id": cat_map["education"],
            "slug": "study-abroad",
            "name_ne": "विदेश अध्ययन परामर्श",
            "name_en": "Study Abroad Consultancy",
            "short_desc_ne": "विदेश अध्ययनका लागि मार्गदर्शन र कागजात।",
            "short_desc_en": "Guidance and documentation for studying abroad.",
        },
    ]

    for s in services:
        db.session.add(Service(**s))

    # Payment methods (with official links)
    payments = [
        {
            "code": "esewa",
            "name_ne": "ई-सेवा",
            "name_en": "eSewa",
            "external_url": "https://esewa.com.np/",
            "logo_url": "https://esewa.com.np/common/images/esewa_logo.png",
            "is_enabled": True,
            "sort_order": 1,
            "instructions_ne": "ई-सेवा मार्फत भुक्तानी गर्नुहोस्। ट्रान्जेक्सन ID पठाउनुहोस्।",
            "instructions_en": "Pay via eSewa and send the transaction ID.",
        },
        {
            "code": "khalti",
            "name_ne": "खल्ती",
            "name_en": "Khalti",
            "external_url": "https://khalti.com/",
            "logo_url": "https://khalti.com/static/images/khalti-logo.png",
            "is_enabled": True,
            "sort_order": 2,
            "instructions_ne": "खल्ती मार्फत भुक्तानी गर्नुहोस्।",
            "instructions_en": "Pay via Khalti.",
        },
        {
            "code": "fonepay",
            "name_ne": "फोनपे",
            "name_en": "Fonepay",
            "external_url": "https://fonepay.com/",
            "logo_url": "https://fonepay.com/assets/images/fonepay-logo.png",
            "is_enabled": True,
            "sort_order": 3,
            "instructions_ne": "फोनपे QR मार्फत भुक्तानी गर्नुहोस्।",
            "instructions_en": "Pay via Fonepay QR.",
        },
        {
            "code": "bank",
            "name_ne": "बैंक ट्रान्सफर",
            "name_en": "Bank Transfer",
            "is_enabled": True,
            "sort_order": 4,
            "instructions_ne": "बैंक खातामा रकम जम्मा गरी स्लिप पठाउनुहोस्।",
            "instructions_en": "Transfer to bank account and send the slip.",
        },
        {
            "code": "cash",
            "name_ne": "नगद / कार्यालय",
            "name_en": "Cash / Office",
            "is_enabled": True,
            "sort_order": 5,
            "instructions_ne": "कार्यालयमा आएर नगद भुक्तानी गर्न सकिन्छ।",
            "instructions_en": "Cash payment can be made at the office.",
        },
    ]
    for p in payments:
        db.session.add(PaymentMethod(**p))

    # Branches
    db.session.add(Branch(
        name_ne="उर्लाबारी शाखा",
        name_en="Urlabari Branch",
        address_ne="राधिका मा वि नजिक, पुरानो तरकारी बजार लाइन, ५ मधुमल्ला रोड, पुष्पनागरी, उर्लाबारी-०५, कोशी प्रदेश, नेपाल",
        address_en="Near Radhika Ma Vi, Old Sabji Bajar Line, 5 Madhumalla Road, Puspanagari, Urlabari-05, Koshi Province, Nepal",
        phone="+977 9713799042",
        email="srallservicenepal@gmail.com",
        whatsapp="+9779713799042",
        hours_ne="बिहान ७:०० – बेलुका ९:००, सोमबारदेखि आइतबारसम्म",
        hours_en="7:00 AM – 9:00 PM, Monday to Sunday",
        is_main=True,
        latitude=26.6635,
        longitude=87.6050,
        sort_order=1,
    ))
    db.session.add(Branch(
        name_ne="काठमाडौं सम्पर्क",
        name_en="Kathmandu Contact",
        phone="+977 9851440623 / +977 9852683942",
        email="srallservicenepal@gmail.com",
        hours_ne="बिहान ७:०० – बेलुका ९:००",
        hours_en="7:00 AM – 9:00 PM",
        sort_order=2,
    ))

    # Homepage sections
    sections = [
        {"key": "announcement", "title_ne": "स्वागत छ", "title_en": "Welcome", "subtitle_ne": "एक प्लेटफर्म। हरेक सेवा। हरेक यात्रा।", "subtitle_en": "One Platform. Every Service. Every Journey.", "is_enabled": True, "sort_order": 1},
        {"key": "hero", "title_ne": "तपाईंको यात्रा, हाम्रो जिम्मेवारी", "title_en": "Your Journey, Our Responsibility", "subtitle_ne": "टिकटदेखि भिसा, टुरदेखि कागजात — सबै एकै ठाउँमा।", "subtitle_en": "From tickets to visas, tours to documentation — all in one place.", "cta_text_ne": "अहिले बुक गर्नुहोस्", "cta_text_en": "Book Now", "cta_url": "/booking", "is_enabled": True, "sort_order": 2},
        {"key": "categories", "title_ne": "हाम्रा सेवा श्रेणीहरू", "title_en": "Our Service Categories", "subtitle_ne": "सात मुख्य श्रेणीमा पूर्ण सेवा", "subtitle_en": "Complete services across seven main categories", "is_enabled": True, "sort_order": 3},
        {"key": "popular", "title_ne": "लोकप्रिय सेवाहरू", "title_en": "Popular Services", "is_enabled": True, "sort_order": 4},
        {"key": "destinations_home", "title_ne": "लोकप्रिय गन्तव्यहरू", "title_en": "Popular Destinations", "subtitle_ne": "तपाईंको अर्को यात्रा यहाँबाट सुरु हुन्छ", "subtitle_en": "Your next journey starts here", "is_enabled": True, "sort_order": 5},
        {"key": "why_us", "title_ne": "किन हामीलाई रोज्ने?", "title_en": "Why Choose Us?", "is_enabled": True, "sort_order": 7},
        {"key": "why_1", "title_ne": "विश्वसनीय", "title_en": "Trusted", "content_ne": "पारदर्शी प्रक्रिया र सुरक्षित कागजात व्यवस्थापन", "content_en": "Transparent process and secure document handling", "is_enabled": True, "sort_order": 71},
        {"key": "why_2", "title_ne": "छिटो सेवा", "title_en": "Fast Service", "content_ne": "अनलाइन बुकिङ र द्रुत प्रतिक्रिया", "content_en": "Online booking and quick response", "is_enabled": True, "sort_order": 72},
        {"key": "why_3", "title_ne": "एकै प्लेटफर्म", "title_en": "One Platform", "content_ne": "टिकट, भिसा, टुर, कागजात — सबै यहाँ", "content_en": "Tickets, visa, tours, documents — all here", "is_enabled": True, "sort_order": 73},
        {"key": "process", "title_ne": "अनलाइन बुकिङ प्रक्रिया", "title_en": "Online Booking Process", "is_enabled": True, "sort_order": 8},
        {"key": "process_1", "title_ne": "सेवा छान्नुहोस्", "title_en": "Choose Service", "content_ne": "आवश्यक सेवा चयन गर्नुहोस्", "content_en": "Select the service you need", "is_enabled": True, "sort_order": 81},
        {"key": "process_2", "title_ne": "फारम भर्नुहोस्", "title_en": "Fill Form", "content_ne": "विवरण र सम्पर्क जानकारी", "content_en": "Details and contact information", "is_enabled": True, "sort_order": 82},
        {"key": "process_3", "title_ne": "ट्र्याक गर्नुहोस्", "title_en": "Track", "content_ne": "रेफरेन्स नम्बरबाट स्थिति", "content_en": "Status via reference number", "is_enabled": True, "sort_order": 83},
        {"key": "process_4", "title_ne": "पुष्टि", "title_en": "Confirm", "content_ne": "भुक्तानी र पुष्टि", "content_en": "Payment and confirmation", "is_enabled": True, "sort_order": 84},
    ]
    for s in sections:
        db.session.add(HomepageSection(**s))

    # FAQs
    faqs = [
        {
            "question_ne": "बुकिङ कसरी ट्र्याक गर्ने?",
            "question_en": "How do I track my booking?",
            "answer_ne": "बुकिङ रेफरेन्स नम्बर र दर्ता गरिएको मोबाइल नम्बर प्रयोग गरी ट्र्याक बुकिङ पेजबाट स्थिति हेर्न सकिन्छ।",
            "answer_en": "Use your booking reference number and registered mobile number on the Track Booking page.",
            "sort_order": 1,
        },
        {
            "question_ne": "भुक्तानी कसरी गर्ने?",
            "question_en": "How can I make payment?",
            "answer_ne": "ई-सेवा, खल्ती, फोनपे, बैंक ट्रान्सफर वा कार्यालयमा नगद मार्फत भुक्तानी गर्न सकिन्छ।",
            "answer_en": "You can pay via eSewa, Khalti, Fonepay, bank transfer or cash at the office.",
            "sort_order": 2,
        },
        {
            "question_ne": "कागजात अपलोड सुरक्षित छ?",
            "question_en": "Is document upload secure?",
            "answer_ne": "हो, कागजातहरू सुरक्षित रूपमा भण्डारण गरिन्छ र केवल अधिकृत कर्मचारीले मात्र पहुँच गर्न सक्छन्।",
            "answer_en": "Yes, documents are stored securely and accessible only to authorized staff.",
            "sort_order": 3,
        },
    ]
    for f in faqs:
        db.session.add(FAQ(**f))

    # Site settings
    settings = [
        {"key": "company_name", "value_ne": "SR All Service Hub Nepal Pvt. Ltd.", "value_en": "SR All Service Hub Nepal Pvt. Ltd."},
        {"key": "tagline", "value_ne": "एक प्लेटफर्म। हरेक सेवा। हरेक यात्रा।", "value_en": "One Platform. Every Service. Every Journey."},
        {"key": "email", "value_ne": "srallservicenepal@gmail.com", "value_en": "srallservicenepal@gmail.com"},
        {"key": "facebook", "value_ne": "https://www.facebook.com/SRallservicehubNepal/", "value_en": "https://www.facebook.com/SRallservicehubNepal/"},
        {"key": "hours", "value_ne": "बिहान ७:०० – बेलुका ९:००, सोमबारदेखि आइतबारसम्म", "value_en": "7:00 AM – 9:00 PM, Monday to Sunday"},
        {"key": "footer_intro_ne", "value_ne": "SR All Service Hub Nepal ले यात्रा, भिसा, कागजात र कर्पोरेट सेवाहरू एकै प्लेटफर्ममा प्रदान गर्दछ।", "value_en": ""},
        {"key": "footer_intro_en", "value_ne": "", "value_en": "SR All Service Hub Nepal provides travel, visa, documentation and corporate services on one platform."},
    ]
    for s in settings:
        db.session.add(SiteSetting(**s))

    # Basic pages
    pages = [
        {
            "slug": "about",
            "title_ne": "हाम्रो बारेमा",
            "title_en": "About Us",
            "content_ne": (
                "SR All Service Hub Nepal Pvt. Ltd. ले यात्रा, भिसा, कागजात, टुर प्याकेज र कर्पोरेट सेवाहरू "
                "एकै प्लेटफर्ममा प्रदान गर्दछ।\n\n"
                "हाम्रो लक्ष्य — तपाईंको हरेक यात्रा र कागजात प्रक्रिया सरल, सुरक्षित र भरपर्दो बनाउनु हो।\n\n"
                "<strong>हामीले दिने सेवा:</strong>\n"
                "• घरेलु तथा अन्तर्राष्ट्रिय उडान टिकट\n"
                "• भिसा सहायता\n"
                "• पुलिस क्लियरेन्स र श्रम स्वीकृति\n"
                "• टुर प्याकेज र होटल बुकिङ\n"
                "• यात्रा बीमा र शिक्षा परामर्श\n\n"
                "Tagline: <em>एक प्लेटफर्म। हरेक सेवा। हरेक यात्रा।</em>"
            ),
            "content_en": (
                "SR All Service Hub Nepal Pvt. Ltd. provides travel, visa, documentation, tour packages "
                "and corporate services on one platform.\n\n"
                "Our goal is to make every journey and paperwork process simple, safe and reliable.\n\n"
                "<strong>Services we offer:</strong>\n"
                "• Domestic and international flight tickets\n"
                "• Visa assistance\n"
                "• Police clearance and labour permit support\n"
                "• Tour packages and hotel booking\n"
                "• Travel insurance and education consultancy\n\n"
                "Tagline: <em>One Platform. Every Service. Every Journey.</em>"
            ),
        },
        {
            "slug": "privacy",
            "title_ne": "गोपनीयता नीति",
            "title_en": "Privacy Policy",
            "content_ne": (
                "<p>SR All Service Hub Nepal Pvt. Ltd. ले तपाईंको व्यक्तिगत जानकारीको सुरक्षा गम्भीरतापूर्वक लिन्छ।</p>"
                "<h3>हामी के जम्मा गर्छौं</h3><ul>"
                "<li>नाम, मोबाइल, इमेल (बुकिङ / सम्पर्क फारमबाट)</li>"
                "<li>सेवा सम्बन्धी विवरण र अपलोड गरिएका कागजात</li>"
                "</ul>"
                "<h3>प्रयोग</h3><p>सेवा प्रदान गर्न, बुकिङ ट्र्याक गर्न, र तपाईंलाई अपडेट पठाउन मात्र प्रयोग गरिन्छ।</p>"
                "<h3>साझेदारी</h3><p>कानूनी आवश्यकता बाहेक तेस्रो पक्षलाई बिक्री गरिँदैन। आधिकारिक प्रक्रियाका लागि मात्र आवश्यक साझेदारसँग साझेदारी हुन सक्छ।</p>"
                "<h3>सम्पर्क</h3><p>srallservicenepal@gmail.com · +977 9713799042</p>"
            ),
            "content_en": (
                "<p>SR All Service Hub Nepal Pvt. Ltd. takes your privacy seriously.</p>"
                "<h3>What we collect</h3><ul>"
                "<li>Name, mobile, email (from booking / contact forms)</li>"
                "<li>Service details and uploaded documents</li>"
                "</ul>"
                "<h3>Use</h3><p>Only to deliver services, track bookings, and send updates.</p>"
                "<h3>Sharing</h3><p>We do not sell your data. Limited sharing may occur with partners only when required for official processes.</p>"
                "<h3>Contact</h3><p>srallservicenepal@gmail.com · +977 9713799042</p>"
            ),
        },
        {
            "slug": "terms",
            "title_ne": "नियम तथा सर्तहरू",
            "title_en": "Terms & Conditions",
            "content_ne": (
                "<p>यस वेबसाइट र सेवा प्रयोग गर्दा तपाईं निम्न सर्तहरूमा सहमत हुनुहुन्छ।</p>"
                "<h3>सेवा</h3><p>हामी टिकट, भिसा सहायता, कागजात, टुर र सम्बन्धित सेवाहरूमा सहयोग गर्छौं। अन्तिम स्वीकृति सम्बन्धित अधिकारी / प्रदायकमा निर्भर हुन्छ।</p>"
                "<h3>बुकिङ</h3><p>अनलाइन बुकिङ अनुरोध हो; पुष्टि भुक्तानी र कागजात जाँच पछि हुन्छ।</p>"
                "<h3>जिम्मेवारी</h3><p>ग्राहकले सही जानकारी र कागजात दिनुपर्छ। गलत विवरणबाट हुने नोक्सानी ग्राहकको जिम्मेवारी हो।</p>"
                "<h3>सम्पर्क</h3><p>srallservicenepal@gmail.com</p>"
            ),
            "content_en": (
                "<p>By using this website and our services you agree to these terms.</p>"
                "<h3>Services</h3><p>We assist with tickets, visas, documentation, tours and related services. Final approval depends on the relevant authority or provider.</p>"
                "<h3>Bookings</h3><p>Online booking is a request; confirmation follows payment and document review.</p>"
                "<h3>Responsibility</h3><p>Customers must provide accurate information and documents.</p>"
                "<h3>Contact</h3><p>srallservicenepal@gmail.com</p>"
            ),
        },
        {
            "slug": "cancellation",
            "title_ne": "रद्द र फिर्ता नीति",
            "title_en": "Cancellation & Refund Policy",
            "content_ne": (
                "<h3>रद्द</h3><p>बुकिङ रद्द गर्न मोबाइल / इमेल मार्फत सम्पर्क गर्नुहोस्। सेवा प्रकार अनुसार नियम फरक हुन सक्छ (उदाहरण: उडान टिकट एयरलाइन नीति अनुसार)।</p>"
                "<h3>फिर्ता</h3><ul>"
                "<li>सेवा सुरु नभएको अवस्थामा: समीक्षा गरी फिर्ता प्रक्रिया सुरु गर्न सकिन्छ</li>"
                "<li>एयरलाइन / तेस्रो पक्ष शुल्क कट्टी हुन सक्छ</li>"
                "<li>फिर्ता ७–१४ कार्य दिनभित्र सम्बन्धित भुक्तानी माध्यममा</li>"
                "</ul>"
                "<h3>सम्पर्क</h3><p>+977 9713799042 · srallservicenepal@gmail.com</p>"
            ),
            "content_en": (
                "<h3>Cancellation</h3><p>Contact us by phone or email to cancel. Rules vary by service (e.g. flight tickets follow airline policy).</p>"
                "<h3>Refunds</h3><ul>"
                "<li>If service has not started: refund may be processed after review</li>"
                "<li>Airline / third-party fees may be deducted</li>"
                "<li>Refunds typically within 7–14 business days to the original payment method</li>"
                "</ul>"
                "<h3>Contact</h3><p>+977 9713799042 · srallservicenepal@gmail.com</p>"
            ),
        },
    ]

    for p in pages:
        db.session.add(Page(**p))

    # Email templates (minimal)
    templates = [
        {
            "key": "booking_received",
            "subject_ne": "बुकिङ प्राप्त भयो – {{booking_id}}",
            "subject_en": "Booking Received – {{booking_id}}",
            "body_ne": "<p>नमस्ते {{customer_name}},</p><p>तपाईंको बुकिङ <strong>{{booking_id}}</strong> प्राप्त भयो। हामी चाँडै सम्पर्क गर्नेछौं।</p><p>ट्र्याक: {{tracking_url}}</p>",
            "body_en": "<p>Hello {{customer_name}},</p><p>Your booking <strong>{{booking_id}}</strong> has been received. We will contact you soon.</p><p>Track: {{tracking_url}}</p>",
        },
        {
            "key": "booking_status_update",
            "subject_ne": "बुकिङ अपडेट – {{booking_id}}",
            "subject_en": "Booking update – {{booking_id}}",
            "body_ne": "<p>नमस्ते {{customer_name}},</p><p>तपाईंको बुकिङ <strong>{{booking_id}}</strong> को नयाँ स्थिति: <strong>{{booking_status}}</strong></p><p>{{note}}</p><p><a href=\"{{tracking_url}}\">ट्र्याक गर्नुहोस्</a></p>",
            "body_en": "<p>Hello {{customer_name}},</p><p>Your booking <strong>{{booking_id}}</strong> is now: <strong>{{booking_status}}</strong></p><p>{{note}}</p><p><a href=\"{{tracking_url}}\">Track booking</a></p>",
        },
        {
            "key": "admin_notification",
            "subject_ne": "नयाँ बुकिङ: {{booking_id}}",
            "subject_en": "New Booking: {{booking_id}}",
            "body_ne": "<p>नयाँ बुकिङ आएको छ: {{booking_id}} – {{service_name}}</p>",
            "body_en": "<p>New booking received: {{booking_id}} – {{service_name}}</p>",
        },
    ]
    for t in templates:
        db.session.add(EmailTemplate(**t))

    
    # Team / Collaborators
    from app.models import TeamMember
    db.session.add(TeamMember(
        name="iZone",
        position_ne="सहकार्य साझेदार",
        position_en="Collaboration Partner",
        bio_ne="SR All Service Hub ले iZone सँग सहकार्य गरेको छ।",
        bio_en="SR All Service Hub collaborates with iZone.",
        is_collaborator=True,
        is_published=True,
        sort_order=10,
    ))
    db.session.add(TeamMember(
        name="BAM Studio",
        position_ne="प्रविधि साझेदार",
        position_en="Technology Partner",
        bio_ne="Technology Partner: BAM Studio",
        bio_en="Technology Partner: BAM Studio",
        is_collaborator=True,
        is_published=True,
        sort_order=11,
    ))

    # Sample destinations
    db.session.add(Destination(slug="pokhara", name_ne="पोखरा", name_en="Pokhara", description_ne="फेवा ताल, साहसिक र हिमाली दृश्य।", description_en="Lakeside, adventure and Himalayan views.", country="Nepal", is_featured=True, is_published=True, sort_order=1))
    db.session.add(Destination(slug="kathmandu", name_ne="काठमाडौं", name_en="Kathmandu", description_ne="साँस्कृतिक राजधानी र सम्पदा।", description_en="Cultural capital and heritage sites.", country="Nepal", is_featured=True, is_published=True, sort_order=2))
    db.session.add(Destination(slug="dubai", name_ne="दुबई", name_en="Dubai", description_ne="अन्तर्राष्ट्रिय व्यापार र पर्यटन गन्तव्य।", description_en="International business and tourism hub.", country="UAE", is_featured=True, is_published=True, sort_order=3))

    db.session.add(Destination(slug="chitwan", name_ne="चितवन", name_en="Chitwan", description_ne="राष्ट्रिय निकुञ्ज र वन्यजन्तु।", description_en="National park and wildlife.", country="Nepal", is_featured=True, is_published=True, sort_order=4))
    db.session.add(Destination(slug="lumbini", name_ne="लुम्बिनी", name_en="Lumbini", description_ne="बुद्ध जन्मस्थल।", description_en="Birthplace of Buddha.", country="Nepal", is_featured=True, is_published=True, sort_order=5))
    db.session.add(Destination(slug="everest", name_ne="एभरेस्ट क्षेत्र", name_en="Everest Region", description_ne="ट्रेकिङ र हिमालय।", description_en="Trekking and Himalayas.", country="Nepal", is_featured=True, is_published=True, sort_order=6))
    db.session.add(Destination(slug="bangkok", name_ne="बैंकक", name_en="Bangkok", description_ne="थाइल्याण्डको राजधानी।", description_en="Capital of Thailand.", country="Thailand", is_featured=True, is_published=True, sort_order=7))
    db.session.add(Destination(slug="delhi", name_ne="दिल्ली", name_en="Delhi", description_ne="भारतको राजधानी क्षेत्र।", description_en="Capital region of India.", country="India", is_featured=False, is_published=True, sort_order=8))




    # Sample packages
    db.session.add(Package(
        slug="pokhara-3d2n",
        title_ne="पोखरा ३ दिन २ रात",
        title_en="Pokhara 3 Days 2 Nights",
        short_desc_ne="फेवा ताल, सराङकोट सूर्योदय, स्थानीय भ्रमण।",
        short_desc_en="Phewa Lake, Sarankot sunrise, local sightseeing.",
        description_ne="पोखराको लोकप्रिय छोटो भ्रमण प्याकेज। होटल, यातायात र गाइड समावेश हुन सक्छ।",
        description_en="Popular short trip to Pokhara. Hotel, transport and guide may be included.",
        price_from=12500,
        currency="NPR",
        duration_days=3,
        is_featured=True,
        is_published=True,
        sort_order=1,
    ))
    db.session.add(Package(
        slug="chitwan-jungle",
        title_ne="चितवन जंगल सफारी",
        title_en="Chitwan Jungle Safari",
        short_desc_ne="२ दिन जंगल सफारी र थारू सांस्कृतिक अनुभव।",
        short_desc_en="2-day jungle safari and Tharu cultural experience.",
        price_from=9000,
        currency="NPR",
        duration_days=2,
        is_featured=True,
        is_published=True,
        sort_order=2,
    ))
    db.session.add(Package(
        slug="kathmandu-heritage",
        title_ne="काठमाडौं सम्पदा भ्रमण",
        title_en="Kathmandu Heritage Tour",
        short_desc_ne="दरबार स्क्वायर, स्वयम्भू, बौद्धनाथ।",
        short_desc_en="Durbar Square, Swayambhu, Boudhanath.",
        price_from=4500,
        currency="NPR",
        duration_days=1,
        is_featured=True,
        is_published=True,
        sort_order=3,
    ))
    db.session.add(Package(
        slug="lumbini-pilgrimage",
        title_ne="लुम्बिनी तीर्थयात्रा",
        title_en="Lumbini Pilgrimage",
        short_desc_ne="बुद्ध जन्मस्थल दर्शन।",
        short_desc_en="Visit the birthplace of Buddha.",
        price_from=7500,
        currency="NPR",
        duration_days=2,
        is_featured=False,
        is_published=True,
        sort_order=4,
    ))

    db.session.commit()
    print("Seed data inserted successfully.")
