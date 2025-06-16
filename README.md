# Star TM1 Project

This is a Flask API + TM1py based tool for extracting TM1 cube and dimension data into a star schema format, for use in Power BI / Tableau / etc.

## Features
- Extract TM1 cube fact tables
- Extract dimension tables
- Serve data via Flask API or save to csv files

## How to run
1. Install `python (3.x)`
2. Install requirements: `pip install -r requirements.txt`
3. Update `config.ini` based on `config.ini.sample`
4. Run `TM1 server` defined in config.ini
5. Run: `python app.py`
6. when using Flask API to directly extract data (Power BI sample):  
	`get Data` -> `Web`:
	input URL (one object each time):  
	`http://<your IP>:<Rest Port>/dimension/<dimension_name>`
	`http://<your IP>:<Rest Port>/cube/<cube_name>`

## Discussion
1.  `Parameter for extract fact data from cube`
		- skip_consolidation : bool  = True          # internal hard coded, no choice
		- skip_zero : bool = True                         # internal hard coded, no choice)
		- skip_rule : bool = False                         # optional, default: False)
		- measures_pivot : bool = True               # True: measures in columns; False: measures in one column plus last column as value)
		- top : int = None                                   # set a small number in testing

2.  `Parameter for extract dimension data from hierarchy`
		 - level_type : int =1                               # 0: TM1 type, 1: TM1py type     


3. `Uneven tree of Dimension-Hierarchy`
		- strongly suggest dimension-hierarchy is even tree (all leaves are in same level).
		- if uneven tree(leaves are in different levels), system will fill the blank level with child element in dimension table, as shown in below pic.	![pic](D:\ibm\tm1py_flask_api\Uneven_tree.png)
4. `Method: File vs Flask`
		 - `Power BI` supports Flask API; if using `Flask` method to extract fact data from cube, it's necessary to set `Content-Type` and `Accept` as : `application/json` in `advanced` setting panel, whilst no need to set for dimension extraction.
		 - `Tableau Desktop` current version doesn't support Flask API （Web connect is depreciated)
		 - Strongly recommend `File` method, because the performance is much better than  `Flask` method.
		
5. `cubes/dimensions setting in config.ini`
		- 'all' for all cubes/dimensions in TM1 system;
		- No parameter or set parameter equals blank means no cube/dimension is indicated;
		- Keep the space in cube/dimension name, like `Sales Analysis`;
		- cube/dimension name is capital sensitive;
		- Use '`,`' between multiple cubes/dimensions; 
