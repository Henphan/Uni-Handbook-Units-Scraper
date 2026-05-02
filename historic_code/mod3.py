with open("full_1800.csv", "r") as f:
    with open("Robot_list.csv", "w") as h:
        for line in f:
            if "" in line:
                print(line)
                # h.write(line)

# with open("ISYS_list.csv", "r") as f:
#     for line in f:
#         if line[4] == '4':
#             print(line)
