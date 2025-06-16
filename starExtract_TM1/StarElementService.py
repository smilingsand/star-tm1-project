import pandas as pd
from TM1py.Services import ElementService, RestService
#from typing import List, Union, Dict, Iterable, Tuple, Optional, Any
#from TM1py.Utils.Utils import CaseAndSpaceInsensitiveSet


# 💦 先来搞定自定义 Element Service
class StarElementService(ElementService):
    def __init__(self, rest: RestService):
        super().__init__(rest)

    def get_elements_star_dataframe(self,
                                    dimension_name, 
                                    hierarchy_name,
                                    skip_attributes = False,
                                    level_type = 0,    # 0: as TM1, 1: as TM1py 
                                    **kwargs
                                ) -> 'pd.DataFrame':

        dfElementInfo = pd.DataFrame()
        dfElementwithParent = pd.DataFrame()

        # judge skip_attributes
        attributes = self.get_element_attribute_names(dimension_name=dimension_name, hierarchy_name=hierarchy_name)
        need_attributes = True if not skip_attributes and len(attributes)>0 else False   

        # get child-parent pairs for all elements
        childParentPair = self.get_parents_of_all_elements(dimension_name=dimension_name, hierarchy_name=hierarchy_name)
        # get total levels count
        levelCount = self.get_levels_count(dimension_name=dimension_name, hierarchy_name=hierarchy_name)

        for level in range(levelCount-1):
            # get child elements
            if level==0:
                # get leaf elements from level 0
                childElements = set(self.get_elements_by_level(dimension_name=dimension_name, hierarchy_name=hierarchy_name, level=level))
            else:
                # get consolidated elements from parent column in previous dfElementwithParent
                childElements = set(dfElementwithParent[f"level{level:03d}"].unique())
            
            # get parent elements  
            parentElements = set(self.get_elements_by_level(dimension_name=dimension_name, hierarchy_name=hierarchy_name, level=level+1))
            
            # find parent from childParentPair for leaf element
            listElementwithParent = [ {'element':ele, 'parent': childParentPair[ele][0] if childParentPair[ele][0] in parentElements else ele } for ele in childElements ] 
            
            # covert child-parent list to child-parent  dataframe            
            dfElementwithParent = pd.DataFrame(listElementwithParent)
            dfElementwithParent.columns = [f"level{level:03d}", f"level{level+1:03d}"]

            # get attributes for child elements
            if need_attributes:
                dfAttrInfo = self.get_elements_dataframe(   dimension_name = dimension_name, 
                                                            hierarchy_name = hierarchy_name,
                                                            elements = childElements,
                                                            attribute_column_prefix = f"level{level:03d}-",
                                                            skip_consolidations = False,
                                                            skip_parents = True,
                                                            skip_weights = True,
                                                            allow_empty_alias = True
                                                        )   
                dfAttrInfo = dfAttrInfo.drop(columns=['Type'])
                dfAttrInfo = dfAttrInfo.replace('', pd.NA).dropna(axis=1, how='all')
                dfAttrInfo = dfAttrInfo.rename(columns={hierarchy_name:f"level{level:03d}"})
                # merge child parent dataframe with child attribites dataframe
                dfElementwithParent = pd.merge( dfElementwithParent,
                                                dfAttrInfo,
                                                on=f"level{level:03d}",   # 以 Element 列为连接键
                                                how='left'                # 左连接
                                               )
                
            if level == 0:
                dfElementInfo = dfElementwithParent
            else:
                dfElementInfo = pd.merge( dfElementInfo,
                                          dfElementwithParent,
                                          on=f"level{level:03d}",   # 以 Element 列为连接键
                                          how='left'                # 左连接
                                        )

        if not dfElementInfo.empty:
            # Sort columns and change columns name to keep consistence with TM1py 
            dfElementInfo = dfElementInfo[sorted(dfElementInfo.columns)]
            dfElementInfo.columns = [ col.replace('level000', hierarchy_name, 1) if col.startswith('level000') else col for col in dfElementInfo.columns ]
            if level_type == 1:  # TM1py type
                # 调整 level 编号
                colCount = max([ int(col[5:8]) if col.startswith('level') else 0 for col in dfElementInfo.columns])
                dfElementInfo.columns = [ "level"+ f"{colCount-int(col[5:8]):03d}" + col[8:] if col.startswith('level') else col  for col in dfElementInfo.columns]

        return dfElementInfo



