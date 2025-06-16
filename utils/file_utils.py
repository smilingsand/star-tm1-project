import os

def export_to_file(dfData, folder='.', cube='', dimension='', hierarchy='', level=0):
	if cube :
		filename = f"Fact_{cube}.csv"
	else:
		filename = f"Dim_{dimension}_{hierarchy}.csv"

	file = os.path.join(folder, filename)
	dfData.to_csv(file, index=False, encoding="utf-8-sig")
	print(f"File {file} saved")