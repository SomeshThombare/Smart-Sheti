# pest_detection/ai_model/solution.py

PEST_SOLUTION_MAP = {
    "rice leaf roller": "Remove folded leaves, use light traps, maintain field sanitation, encourage natural enemies, and spray neem-based bio-pesticide.",
    "rice leaf caterpillar": "Remove affected leaves, avoid excess nitrogen fertilizer, use pheromone traps, and spray neem extract.",
    "paddy stem maggot": "Use healthy seedlings, remove infected tillers, maintain proper water level, and avoid late transplanting.",
    "asiatic rice borer": "Destroy crop stubbles after harvest, remove dead hearts, use pheromone traps, and maintain field sanitation.",
    "yellow rice borer": "Use resistant varieties, remove infected stems, avoid excess nitrogen, and destroy crop residues.",
    "rice gall midge": "Use resistant rice varieties, remove affected plants, avoid staggered planting, and keep the field clean.",
    "Rice Stemfly": "Remove infested shoots, avoid dense sowing, maintain field hygiene, and use neem-based spray.",
    "brown plant hopper": "Avoid excess nitrogen fertilizer, drain water periodically, use resistant varieties, and conserve natural enemies.",
    "white backed plant hopper": "Avoid overcrowding, reduce nitrogen fertilizer, monitor crop base regularly, and use neem-based spray.",
    "small brown plant hopper": "Keep field clean, avoid excessive irrigation, monitor early symptoms, and use yellow sticky traps.",
    "rice water weevil": "Use clean seedlings, drain field temporarily, remove weeds, and rotate crops.",
    "rice leafhopper": "Use resistant varieties, remove weeds, avoid excess nitrogen, and use yellow sticky traps.",
    "grain spreader thrips": "Maintain proper irrigation, remove weeds, spray neem oil, and monitor young crop stage.",
    "rice shell pest": "Remove infected rice panicles, maintain field hygiene, avoid excess nitrogen, use light traps, and monitor crop regularly.",
    "grub": "Do deep ploughing, expose larvae to birds, apply well-decomposed manure, and use neem cake in soil.",
    "mole cricket": "Do deep ploughing, destroy tunnels, use light traps, and apply neem cake near roots.",
    "wireworm": "Use crop rotation, deep summer ploughing, remove weeds, and apply neem cake in soil.",
    "white margined moth": "Remove larvae manually, use light traps, destroy affected leaves, and spray neem extract.",
    "black cutworm": "Remove weeds, do deep ploughing, collect larvae during evening, and use pheromone traps.",
    "large cutworm": "Keep field clean, do deep ploughing, handpick larvae, and use neem-based bio-pesticide.",
    "yellow cutworm": "Destroy crop residues, use light traps, do deep ploughing, and monitor seedlings regularly.",
    "red spider": "Maintain moisture, avoid dusty conditions, spray water on leaves, and apply neem oil.",
    "corn borer": "Remove affected shoots, use pheromone traps, destroy crop residues, and use resistant hybrids.",
    "army worm": "Monitor crop at night, handpick larvae, use light traps, and apply neem extract.",
    "aphids": "Use yellow sticky traps, spray neem oil, avoid excess nitrogen, and encourage ladybird beetles.",
    "Potosiabre vitarsis": "Collect adult beetles manually, use light traps, maintain field sanitation, and destroy damaged plant parts.",
    "peach borer": "Remove infested branches, clean bark cracks, use pheromone traps, and maintain tree health.",
    "english grain aphid": "Use yellow sticky traps, conserve ladybird beetles, avoid excess nitrogen, and spray neem oil.",
    "green bug": "Monitor leaves regularly, use resistant varieties, conserve natural enemies, and apply neem-based spray.",
    "bird cherry-oat aphid": "Remove weeds, avoid excess nitrogen, use yellow sticky traps, and encourage natural predators.",
    "wheat blossom midge": "Use early sowing, resistant varieties, crop rotation, and destroy volunteer wheat plants.",
    "penthaleus major": "Maintain field moisture, remove weeds, use crop rotation, and apply neem-based spray.",
    "longlegged spider mite": "Avoid drought stress, spray water regularly, remove infested leaves, and use neem oil.",
    "wheat phloeothrips": "Use clean seed, remove weeds, maintain irrigation, and spray neem extract.",
    "wheat sawfly": "Use resistant varieties, do deep ploughing, destroy stubbles, and rotate crops.",
    "cerodonta denticornis": "Remove affected leaves, destroy crop residues, monitor early damage, and use neem spray.",
    "beet fly": "Remove infested leaves, use yellow sticky traps, destroy crop residues, and maintain field sanitation.",
    "flea beetle": "Use sticky traps, cover young plants, remove weeds, and apply neem oil.",
    "cabbage army worm": "Handpick larvae, use pheromone traps, destroy egg masses, and spray neem extract.",
    "beet army worm": "Monitor leaves, remove larvae, use pheromone traps, and use biological control.",
    "Beet spot flies": "Remove affected leaves, maintain field hygiene, use sticky traps, and avoid dense planting.",
    "meadow moth": "Use light traps, remove larvae, maintain clean field, and spray neem extract.",
    "beet weevil": "Use crop rotation, do deep ploughing, remove weeds, and collect adults manually.",
    "sericaorient alismots chulsky": "Do deep ploughing, use light traps, apply neem cake, and maintain soil hygiene.",
    "alfalfa weevil": "Cut crop early if infestation is high, remove larvae, conserve natural enemies, and use neem spray.",
    "flax budworm": "Remove damaged buds, use pheromone traps, destroy crop residue, and apply neem extract.",
    "alfalfa plant bug": "Remove weeds, monitor field regularly, avoid excess nitrogen, and use neem-based spray.",
    "tarnished plant bug": "Remove weeds near field, monitor flowers, use sticky traps, and maintain field sanitation.",
    "Locustoidea": "Monitor early, destroy egg beds, use trap crops, and coordinate community control.",
    "lytta polita": "Handpick beetles carefully, use light traps, remove weeds, and maintain field sanitation.",
    "legume blister beetle": "Use trap crops, remove flowering weeds, collect beetles carefully, and spray neem extract.",
    "blister beetle": "Collect beetles carefully with gloves, remove weeds, use light traps, and spray neem extract.",
    "therioaphis maculata Buckton": "Use resistant varieties, conserve ladybird beetles, use yellow sticky traps, and spray neem oil.",
    "odontothrips loti": "Use blue sticky traps, maintain irrigation, remove weeds, and spray neem-based bio-pesticide.",
    "Thrips": "Use blue sticky traps, remove weeds, maintain humidity, and apply neem oil.",
    "alfalfa seed chalcid": "Use clean seed, destroy infested pods, rotate crops, and harvest on time.",
    "Pieris canidia": "Remove eggs and larvae manually, use net protection, spray neem extract, and encourage parasitoids.",
    "Apolygus lucorum": "Use sticky traps, remove weeds, monitor young shoots, and spray neem-based bio-pesticide.",
    "Limacodidae": "Handpick larvae, remove affected leaves, use light traps, and spray neem extract.",
    "Viteus vitifoliae": "Use resistant rootstock, remove infected leaves, avoid moving infected plant material, and maintain vineyard hygiene.",
    "Colomerus vitis": "Prune affected parts, maintain vineyard hygiene, remove infected leaves, and use neem/sulfur spray as locally advised.",
    "Brevipoalpus lewisi McGregor": "Remove infested leaves, avoid dust, maintain irrigation, and use neem oil.",
    "oides decempunctata": "Handpick beetles, remove damaged leaves, use light traps, and spray neem extract.",
    "Polyphagotarsonemus latus": "Remove infested shoots, avoid excess nitrogen, maintain humidity, and use neem oil.",
    "Pseudococcus comstocki Kuwana": "Remove infected branches, control ants, use sticky bands, and spray neem oil.",
    "parathrene regalis": "Prune infested shoots, destroy larvae, use pheromone traps, and maintain plant hygiene.",
    "Ampelophaga": "Handpick larvae, use light traps, prune affected leaves, and apply neem extract.",
    "Lycorma delicatula": "Destroy egg masses, use sticky bands, remove host weeds, and report severe infestation to agriculture authorities.",
    "Xylotrechus": "Prune and destroy infested branches, avoid plant stress, use traps, and maintain orchard hygiene.",
    "Cicadella viridis": "Remove weeds, use yellow sticky traps, avoid excess nitrogen, and spray neem extract.",
    "Miridae": "Use sticky traps, remove weeds, monitor tender shoots, and conserve natural enemies.",
    "Trialeurodes vaporariorum": "Use yellow sticky traps, remove infected leaves, control weeds, and spray neem oil.",
    "Erythroneura apicalis": "Use sticky traps, remove weeds, maintain plant vigor, and use neem-based spray.",
    "Papilio xuthus": "Handpick larvae, remove eggs, use net protection, and spray neem extract.",
    "Panonchus citri McGregor": "Spray water to reduce mites, remove infested leaves, avoid dust, and use neem oil.",
    "Phyllocoptes oleiverus ashmead": "Prune infected parts, maintain orchard sanitation, remove infested leaves, and use neem/sulfur spray as locally advised.",
    "Icerya purchasi Maskell": "Control ants, prune infested branches, use neem oil, and conserve natural enemies.",
    "Unaspis yanonensis": "Prune infected twigs, use neem or horticultural oil, control ants, and maintain tree health.",
    "Ceroplastes rubens": "Remove scale insects manually, prune branches, control ants, and apply neem oil.",
    "Chrysomphalus aonidum": "Prune infested leaves, use oil spray, control ants, and maintain orchard hygiene.",
    "Parlatoria zizyphus Lucus": "Remove affected twigs, use neem oil spray, control ants, and avoid overcrowding.",
    "Nipaecoccus vastalor": "Control ants, prune infected parts, use sticky bands, and apply neem oil.",
    "Aleurocanthus spiniferus": "Use yellow sticky traps, prune affected leaves, spray neem oil, and conserve parasitoids.",
    "Tetradacus c Bactrocera minax": "Collect and destroy fallen fruits, use fruit fly traps, bag fruits, and maintain orchard sanitation.",
    "Dacus dorsalis(Hendel)": "Use methyl eugenol traps, destroy fallen fruits, bag fruits, and maintain orchard sanitation.",
    "Bactrocera tsuneonis": "Use fruit fly traps, collect fallen fruits, bag fruits, and keep orchard clean.",
    "Prodenia litura": "Destroy egg masses, use pheromone traps, handpick larvae, and spray neem extract.",
    "Adristyrannus": "Remove damaged plant parts, use light traps, maintain field sanitation, and use neem spray.",
    "Phyllocnistis citrella Stainton": "Prune affected flushes, avoid excess nitrogen, use neem oil, and conserve parasitoids.",
    "Toxoptera citricidus": "Use yellow sticky traps, remove infected shoots, conserve ladybird beetles, and spray neem oil.",
    "Toxoptera aurantii": "Control ants, use sticky traps, prune infected shoots, and apply neem oil.",
    "Aphis citricola Vander Goot": "Use yellow sticky traps, control ants, avoid excess nitrogen, and spray neem oil.",
    "Scirtothrips dorsalis Hood": "Use blue sticky traps, prune infested shoots, maintain irrigation, and spray neem oil.",
    "Dasineura sp": "Remove affected plant parts, destroy infested shoots, maintain orchard hygiene, and monitor new flush.",
    "Lawana imitata Melichar": "Remove infected shoots, use sticky traps, maintain plant hygiene, and apply neem-based spray.",
    "Salurnis marginella Guerr": "Remove affected leaves, use yellow sticky traps, control weeds, and use neem spray.",
    "Deporaus marginatus Pascoe": "Collect and destroy rolled leaves, prune affected shoots, and maintain orchard sanitation.",
    "Chlumetia transversa": "Remove damaged shoots, use pheromone or light traps, destroy larvae, and apply neem extract.",
    "Mango flat beak leafhopper": "Prune dense canopy, use yellow sticky traps, avoid excess nitrogen, and spray neem oil.",
    "Rhytidodera bowrinii white": "Prune infested branches, destroy larvae, maintain tree health, and avoid bark injuries.",
    "Sternochetus frigidus": "Collect fallen fruits, destroy infected seeds, maintain orchard sanitation, and use traps.",
    "Cicadellidae": "Use yellow sticky traps, remove weeds, avoid excess nitrogen, and apply neem-based spray.",
}


DEFAULT_SOLUTION = (
    "Proper solution not available. Please contact nearby agriculture expert or Krishi Seva Kendra."
)


def normalize_pest_name(pest_name):
    if not pest_name:
        return ""

    pest_name = str(pest_name).strip()
    pest_name = " ".join(pest_name.split())

    return pest_name.lower()


NORMALIZED_PEST_SOLUTIONS = {
    normalize_pest_name(key): value
    for key, value in PEST_SOLUTION_MAP.items()
}


def get_pest_solution(pest_name):
    normalized_name = normalize_pest_name(pest_name)

    return NORMALIZED_PEST_SOLUTIONS.get(
        normalized_name,
        DEFAULT_SOLUTION
    )