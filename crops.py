def crop(crop_name):
    crop_data = {
        "maize": ["/static/images/maize.jpg", "Ashanti, Brong-Ahafo, Northern", "Major/Minor", "Burkina Faso, Togo, Benin"],
        "cassava": ["/static/images/cassava.jpg", "Eastern, Central, Ashanti", "Year-round", "Europe, USA, China"],
        "rice_local": ["/static/images/paddy.jpg", "Northern, Volta, Upper East", "Major", "Local Consumption"],
        "rice_imported": ["/static/images/rice.jpg", "All Regions (Imported)", "N/A", "Vietnam, Thailand, India"],
        "yam": ["/static/images/yam.jpg", "Brong-Ahafo, Northern, Ashanti", "Major", "Europe, USA, Nigeria"],
        "tomatoes_local": ["/static/images/tomatoes.jpg", "Upper East, Ashanti, Brong-Ahafo", "Major/Minor", "Togo, Burkina Faso"],
        "tomatoes_navrongo": ["/static/images/tomatoes.jpg", "Upper East (Navrongo)", "Major", "Burkina Faso"],
        "onions": ["/static/images/onions.jpg", "Upper East, Northern", "Major", "Niger, Burkina Faso"],
        "eggplants": ["/static/images/eggplant.jpg", "Ashanti, Eastern, Central", "Major/Minor", "Regional Markets"],
        "gari": ["/static/images/gari.jpg", "Central, Eastern, Volta", "Year-round", "Europe, USA, Nigeria"],
        "plantains_apentu": ["/static/images/plantain.jpg", "Ashanti, Brong-Ahafo, Western", "Major/Minor", "Europe, USA"],
        "plantains_apem": ["/static/images/plantain.jpg", "Ashanti, Eastern", "Major/Minor", "Regional Markets"],
        "sorghum": ["/static/images/sorghum.jpg", "Northern, Upper West, Upper East", "Major", "Local Consumption"],
        "soybeans": ["/static/images/soybeans.jpg", "Northern, Upper West", "Major", "Asia, Europe"],
        "millet": ["/static/images/millet.jpg", "Upper East, Northern", "Major", "Local Consumption"],
        "cowpeas": ["/static/images/cowpeas.jpg", "Northern, Upper West", "Major", "Regional Markets"],
        "peppers_fresh": ["/static/images/peppers.jpg", "Ashanti, Volta, Central", "Major/Minor", "Europe"],
        "peppers_dried": ["/static/images/peppers.jpg", "Northern, Upper West", "Year-round", "Europe, Regional Markets"],
        "yam_puna": ["/static/images/yam.jpg", "Northern, Brong-Ahafo", "Major", "International Export"],
        "eggs": ["/static/images/eggs.jpg", "Ashanti, Greater Accra", "Year-round", "Regional Markets"],
        "maize_yellow": ["/static/images/maize.jpg", "Northern, Brong-Ahafo", "Major", "Local Consumption"],
        "rice_paddy": ["/static/images/paddy.jpg", "Volta, Northern", "Major", "Local Processing"],
        "cowpeas_white": ["/static/images/cowpeas.jpg", "Northern, Upper West", "Major", "Local Consumption"],
        "fish_mackerel_fresh": ["/static/images/fish.jpg", "Greater Accra, Central, Western", "Year-round", "Regional Markets"],
        "meat_chicken_local": ["/static/images/chicken.jpg", "All Regions", "Year-round", "Local Consumption"],
        "meat_chicken": ["/static/images/chicken.jpg", "Greater Accra, Ashanti", "Year-round", "Imports from EU/Brazil"]
    }
    
    # Try to find the closest match or default
    clean_name = crop_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')
    if clean_name in crop_data:
        return crop_data[clean_name]
    return ["/static/images/default.jpg", "Ghana", "Varies", "Global"]