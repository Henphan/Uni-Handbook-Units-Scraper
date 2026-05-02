with open("all_units.csv", "r") as f:
    with open("CMPE.csv", "w") as g:
        for line in f:
            if "CMPE" in line or "CMPE" in line:
                g.write(line)