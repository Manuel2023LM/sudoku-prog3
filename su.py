cols="ABCDEFGHI"
rows="123456789"
# import itertools as it
vars=[f"{col}{row}" for row in rows for col in cols]
print(vars)

VarsDoms={var:set(range(1,10)) for var in vars}
VarsDoms

with open('/content/MuyFacil','r') as f:
  pos=0
  for line in f.readlines():
    if int(line)<10:
      VarsDoms[vars[pos]]={int(line)}
    pos+=1
VarsDoms

RowsVarsList=[[f"{col}{row}" for col in cols] for row in rows]
RowsVarsList

ColsVarsList=[[f"{col}{row}" for row in rows] for col in cols]
ColsVarsList

ConstraintsVarsLists=RowsVarsList+ColsVarsList
ConstraintsVarsLists


def AllDif(VarsDoms,VarsList):
  for varSrc in VarsList:
    if len(VarsDoms[varSrc])==1:
      for varDst in VarsList:
        if varSrc!=varDst:
          VarsDoms[varDst]=VarsDoms[varDst]-VarsDoms[varSrc]

def ExcValue(VarsDoms,VarsList):
  for varSrc in VarsList:
    if len(VarsDoms[varSrc])>1:
      U=set()
      for varDst in VarsList:
        if varSrc!=varDst:
          if len(VarsDoms[varDst])>1:
            U=U.union(VarsDoms[varDst])
      Dif=VarsDoms[varSrc]-U
      if len(Dif)==1:
        VarsDoms[varSrc]=Dif



AllDif(VarsDoms,['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1'])
VarsDoms



for constraint in ConstraintsVarsLists:
  AllDif(VarsDoms,constraint)
  ExcValue(VarsDoms,constraint)
VarsDoms


for constraint in ConstraintsVarsLists:
  AllDif(VarsDoms,constraint)
VarsDoms