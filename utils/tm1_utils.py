# tm1_utils.py
import numpy as np
import pandas as pd
import fnmatch
from datetime import datetime
from .file_utils import export_to_file
from starExtract_TM1 import StarTM1Service


class TM1:
    def __init__(self, config):
        self.config=config
        self.tm1server=config.get('OVERALL','TM1-Server')
        self.tm1 = StarTM1Service(
            address=config.get(self.tm1server, 'address'),
            port=config.getint(self.tm1server, 'port'),
            user=config.get(self.tm1server, 'user'),
            password=config.get(self.tm1server, 'password'),
            ssl=config.getboolean(self.tm1server, 'ssl'),
            verify=False
        )
        self.cubes=set()
        self.dimensions=set()
        self.create_cube_list()
        self.create_dimension_list()

    def create_cube_list(self):
        selectedCubes = set()

        # 从config文件中获取cube list
        if self.config.has_option(self.tm1server, 'cubes'):
            inputString = self.config.get(self.tm1server, 'cubes').strip()
            if inputString:
                if inputString.lower() == 'all':
                    # 获取 所有的 user defined cubes list
                    allCubes = self.tm1.cubes.get_all_names()
                    # remove control cubes
                    selectedCubes = [x for x in allCubes if not x.startswith('}')]
                else:
                    # 获取 cubes参数的cubes list
                    selectedCubes = {item.strip() for item in inputString.split(',') }
                    # 除去系统中不存在的cube
                    selectedCubes = { cube for cube in selectedCubes if self.tm1.cubes.exists(cube) }

        self.cubes = selectedCubes
        # print("selectedCubes:" , selectedCubes)
        return 


    def create_dimension_list(self):
        selectedDims = set()

        # create dimension list for selected cubes
        selectedDims_cubes = set()
        if len(self.cubes)>0 :
            # 获取 cubes参数对应的dimensions list
            for cube in self.cubes:
                measureDim = self.tm1.cubes.get_measure_dimension(cube_name=cube) 
                AllDims = self.tm1.cubes.get_dimension_names(cube_name=cube, skip_sandbox_dimension=True) 
                selectedDims_cubes = selectedDims_cubes | set([dim for dim in AllDims if dim != measureDim ])

        # create dimension list for selected dimensions          
        selectedDims_dimensions = set()
        if self.config.has_option(self.tm1server, 'dimensions'):
            inputString = self.config.get(self.tm1server, 'dimensions').strip()
            if inputString: 
                if inputString.lower() == 'all':
                    # 获取 所有的 user defined dimensions list
                    allDims = self.tm1.dimensions.get_all_names()
                    # remove control dimensions
                    selectedDims_dimensions = { x for x in allDims if not x.startswith('}') }
                else:
                    # 获取 dimensions参数的dimensions list
                    selectedDims_dimensions = { item.strip() for item in inputString.split(',') }
                    # 除去系统中不存在的dimensions
                    selectedDims_dimensions = { dim for dim in selectedDims_dimensions if self.tm1.dimensions.exists(dim) }


        # 取并集
        selectedDims = selectedDims_cubes | selectedDims_dimensions
        selectedDims = { x for x in selectedDims if not x.startswith('}') }  #有必要吗? 为什么不能做control dimension？

        if len (selectedDims) > 0:
            # Filter selectedDims according to 参数dimensions_neglect定义
            if self.config.has_option(self.tm1server, 'dimensions_neglect') :
                dimensions_neglect = self.config.get(self.tm1server, 'dimensions_neglect').strip()
                if dimensions_neglect:
                    # 将 pattern 字符串转为 pattern 列表
                    patterns = [p.strip() for p in dimensions_neglect.split(',')]
                    # 过滤函数
                    selectedDims = { item for item in selectedDims
                                     if not any(fnmatch.fnmatch(item, pattern) for pattern in patterns)
                                   }

        self.dimensions = selectedDims
        return


    def extract_cubes(self, skip_rule_derived_cells: bool = False, measures_pivot: bool = False, top: int = None):
        for cube in self.cubes:             
            start_time = datetime.now()
            print(f"Start at {start_time.strftime('%Y-%m-%d %H:%M:%S')} to extract data for cube {cube}") 

            dfCubeData = self.extract_cube( cube=cube, 
                                            top=top, 
                                            skip_rule_derived_cells = skip_rule_derived_cells,
                                            measures_pivot = measures_pivot
                                          )

            end_time = datetime.now()
            duration = end_time - start_time
            print(f"Finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}, Total time taken: {duration.total_seconds():.2f} seconds")

            if not dfCubeData.empty :
                self.export(cube=cube, dfData=dfCubeData)
            else:
                print(f"No data extracted for cube {cube}")



    def extract_cube(self, cube: str = None, measures_pivot: bool = False, skip_rule_derived_cells: bool = False, top: int = None):
        self.cubes = {cube}
        dfCubeData = self.tm1.cells.get_fact_dataframe(
                                            cube=cube, 
                                            top=top,
                                            skip_zeros = True,
                                            skip_consolidated_cells = True,
                                            skip_rule_derived_cells = skip_rule_derived_cells,
                                            measures_pivot = measures_pivot
                                            )
        #print(dfCubeData) 
        return dfCubeData      


    def extract_dimensions(self, level_type=0):       # level_type 0: TM1 type, 1: TM1py type 
        dfDimensionData_group = dict()

        for dimension_name in self.dimensions: 
            # get Hierarchy Name
            for hierarchy_name in self.tm1.hierarchies.get_all_names(dimension_name=dimension_name):            
                dfDimensionData = self.extract_hierarchy( dimension_name=dimension_name, 
                                                          hierarchy_name=hierarchy_name, 
                                                          level_type=level_type
                                                        )

                if not dfDimensionData.empty :
                    # Export
                    self.export(dimension=dimension_name, hierarchy=hierarchy_name, dfData=dfDimensionData)
                    # build dfDimensionData_group
                    dfDimensionData_group[f"{dimension_name}-{hierarchy_name}"] = dfDimensionData
                else:
                    print(f"No data extracted for hirarchy {dimension_name}-{hierarchy_name}")
        #print("dfDimensionData_group ->", dfDimensionData_group)
        return dfDimensionData_group


    def extract_hierarchy(self, dimension_name, hierarchy_name, level_type=0):    # 0: TM1 type, 1: TM1py type 
        print(f'Start to extract dimension information for {dimension_name}-{hierarchy_name}')
        dfDimensionData = self.tm1.elements.get_elements_star_dataframe(  
                                                    dimension_name=dimension_name, 
                                                    hierarchy_name=hierarchy_name,
                                                    skip_attributes=False,
                                                    level_type=level_type  
                                                    )
        #print(dfDimensionData)
        return dfDimensionData


    def export(self, dfData, cube='', dimension='', hierarchy='', level=0):
        if self.config.get('OVERALL', 'ExportMethod').lower() == 'file':
            folder = self.config.get('FILE', 'folder')
            if cube:
                export_to_file(folder=folder, cube=cube, dfData=dfData)
            else:
                export_to_file(folder=folder, dimension=dimension, hierarchy=hierarchy, dfData=dfData)
