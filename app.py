# app.py
import configparser
#from tm1_utils_1 import TM1
from utils.tm1_utils import TM1
from flask import Flask, jsonify, request, Response
import json


# 初始化 Flask
app = Flask(__name__)

# 全局变量
config = configparser.ConfigParser()
tm1 = None


@app.route('/cubewithdims/<cube_name>')
def get_fact_and_Dims(cube_name):
    # get cube name from input
    input_cube = cube_name
    tm1.cubes={input_cube}
    tm1.create_dimension_list()
    print("tm1.dimensions:", tm1.dimensions)
    data = dict()

    if tm1.tm1.cubes.exists(input_cube):
        # retrieve cube data
        top = request.args.get('top', default=None, type=int)
        dfData = tm1.extract_cube(  cube=input_cube, 
                                    top=top,          # top=100 for test
                                    skip_rule_derived_cells = False,
                                    measures_pivot=True                            
                                    ) 
        data[input_cube] = dfData.to_dict(orient='records')

        # retrieve dimensions data
        dfDimensionData_group = tm1.extract_dimensions(level_type=1) 
        for hierarchy in dfDimensionData_group.keys():
            dfData = dfDimensionData_group[hierarchy]
            data[hierarchy] = dfData.to_dict(orient='records')

        return jsonify(data)
        # 需要在PBI的'get Data'->'Advanced'的页面中设置'Accept'和'Content-Type'为'application/json'，才能让PBI正确解读json数据。

    else:
        return jsonify({'error': f"cube {cube} not found"}), 404


@app.route('/cube/<cube_name>')
def get_fact(cube_name):
    # get cube name from input
    input_cube = cube_name
    if tm1.tm1.cubes.exists(input_cube):
        top = request.args.get('top', default=None, type=int)
        dfData = tm1.extract_cube(  cube=input_cube, 
                                    top=top,          # top=100 for test
                                    skip_rule_derived_cells = False,
                                    measures_pivot=True                                     
                                    ) 
        # Json export for Power BI
        data = dfData.to_dict(orient='records')
        return jsonify(data)
        # 需要在PBI的'get Data'->'Advanced'的页面中设置'Accept'和'Content-Type'为'application/json'，才能让PBI正确解读json数据。
        '''
        # csv export for Power BI/tableau
        csv_data = dfData.to_csv(index=False)
        return Response( csv_data,
                         mimetype='text/csv'
                       )
        '''
    else:
        return jsonify({'error': f"cube {cube} not found"}), 404


@app.route('/dimension/<dimension_name>')
def get_dimension(dimension_name):
    input_dimension = dimension_name
    if tm1.tm1.dimensions.exists(input_dimension): 
        dfData = tm1.extract_hierarchy( dimension_name=input_dimension, 
                                        hierarchy_name=input_dimension, 
                                        level_type=1    # level_type   0: TM1 type, 1: TM1py type  
                                       )  

        # Json export for Power BI
        data = dfData.to_dict(orient='records')
        return jsonify(data)
        '''
        # csv export for Power BI/tableau
        csv_data = dfData.to_csv(index=False)
        return Response( csv_data,
                         mimetype='text/csv'
                       )
        '''
    else:
        return jsonify({'error': f"Dimension {input_dimension} not found"}), 404



def run_flask_mode():
    app.run( host=config.get('FLASK', 'host'),
             port=config.getint('FLASK', 'port'),
             debug=config.getboolean('FLASK', 'debug')
            )



def run_file_mode():
    # Extract dimension tables and fact table at startup
    tm1.extract_dimensions(level_type=1)               # level_type   0: TM1 type, 1: TM1py type 
    tm1.extract_cubes( # top=100,                      # top=100 for test  
                       skip_rule_derived_cells = False,
                       measures_pivot=True
                     )  




def main():
    global config, tm1
    config.read('config.ini')
    tm1 = TM1(config)

    export_method = config.get('OVERALL', 'ExportMethod').lower()
    if export_method == 'file': 
        run_file_mode()
    elif export_method == 'flask': 
        run_flask_mode()
    else:
        print(f"Unsupported ExportMethod: {export_method}")



if __name__ == '__main__':
    main()