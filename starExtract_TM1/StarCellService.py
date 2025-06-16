from TM1py.Services import CellService, RestService
from TM1py.Utils.Utils import CaseAndSpaceInsensitiveSet
from typing import List, Union, Dict, Iterable, Tuple, Optional, Any

class StarCellService(CellService):
    def __init__(self, rest: RestService):
        super().__init__(rest)


    def get_fact_dataframe(    self, 
                                      cube: str = None,
                                      top: int = None, 
                                      skip: int = None,
                                      skip_zeros: bool = True,
                                      skip_consolidated_cells: bool = False, 
                                      skip_rule_derived_cells: bool = False,
                                      sandbox_name: str = None, 
                                      include_attributes: bool = False,
                                      use_iterative_json: bool = False, 
                                      use_compact_json: bool = False,
                                      use_blob: bool = False, 
                                      shaped: bool = False, 
                                      mdx_headers: bool = False,
                                      fillna_numeric_attributes: bool = False,
                                      fillna_numeric_attributes_value: Any = 0,
                                      fillna_string_attributes: bool = False,
                                      fillna_string_attributes_value: Any = '',
                                      measures_pivot = False,
                                      **kwargs
                                    ) -> 'pd.DataFrame':
        
        # get dimension information of cube
        cube_service = self.get_cube_service()
        measureDim = cube_service.get_measure_dimension(cube_name=cube)
        AllDims = CaseAndSpaceInsensitiveSet(*cube_service.get_storage_dimension_order(cube_name=cube))
        otherDims = [ dim for dim in AllDims if dim != measureDim ]
        #print(f"cube: {cube} - measure_dimension: {measureDim}")
        #print(f"cube: {cube} - all_dimension: {AllDims}")
        #print(f"cube: {cube} - other_dimension: {otherDims}")

        # build mdx to extract fact data
        mdx_rows_string = ''
        for dim in otherDims:
            starString = '   ' if len(mdx_rows_string) == 0 else ' * '
            mdx_rows_string = mdx_rows_string + starString + f" TM1FILTERBYLEVEL({{TM1SUBSETALL([{dim}])}}, 0)  "              # formal code

        mdx = f'''  SELECT 
                        NON EMPTY {{  TM1SUBSETALL([{measureDim}]) 
                                  }}  ON COLUMNS,
                        NON EMPTY {{  {mdx_rows_string}
                                  }}  ON ROWS
                        FROM [{cube}] 
               '''
        #print(mdx)   

       
        dfData = self.execute_mdx_dataframe(   
                            mdx = mdx,
                            top = top,
                            skip = skip,
                            skip_zeros = skip_zeros,
                            skip_consolidated_cells = skip_consolidated_cells,
                            skip_rule_derived_cells = skip_rule_derived_cells
                            )     


        if measures_pivot :
            # pivot and export
            columns = dfData.columns.tolist()
            if columns and len(columns)>2:
                # pivot
                # 无论你写的 MDX 是多维交叉表（ROWS x COLUMNS）还是组合查询，execute_mdx_dataframe() 总是把所有维度都拆成 DataFrame 的列。
                # 原来你在 MDX 的 COLUMNS 区里那些维度，它也会被当成 新的一列 放在 DataFrame 里。 所以需要pivot。
                dfData = dfData.pivot(index=columns[:-2], columns=columns[-2], values=columns[-1]).reset_index()


        return dfData




