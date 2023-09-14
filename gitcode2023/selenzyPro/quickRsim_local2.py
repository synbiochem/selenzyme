'''
quickRsim (c) University of Manchester 2017

quickRsim is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  Pablo Carbonell, SYNBIOCHEM
@description: Compute a fast reaction similarity with the database
@examples: 
1. Compute similarity to one reaction in the database (requires -chem parameter)
python quickRsim.py data/reac_prop.tsv data/metanetx.fs -rid MNXR3215 -chem data/chem_prop.tsv
2. Compute similarity to a given reaction file for a threshold above 0.9
python quickRsim.py data/reac_prop.tsv data/metanetx.fs -rxn rhea15870.rxn -th 0.9
'''

from __future__ import print_function
import argparse
import subprocess
import os
from rdkit.Chem import rdChemReactions
import math
import numpy as np
from rdkit import DataStructs, Chem
from rdkit.Chem.rdMolDescriptors import GetMorganFingerprint 
from rdkit.Chem.rdmolops import PatternFingerprint, RDKFingerprint
from rdkit.Chem import AllChem
from mcs_functions2 import reactFragDists, process_compF
from rxnmapper import RXNMapper
from rdkit.Chem import Draw
import mcs_functions2
from statistics import mean 



def fingerprint():
    """ I keep the three fingerprints that give better results in the tests """
    fpd =  {'Pattern': ('ptfp', None, True, PatternFingerprint, 2), 'RDK': ('rdkfp', None, True, RDKFingerprint, 1),
            'Morgan' : ('FP_Morg', 5, False, GetMorganFingerprint, 3)}
    fpd =  {'Morgan' : ('FP_Morg', 5, False, GetMorganFingerprint, 3)}
    return fpd



def loadFingerprint(datadir, fpid):
    fpi = fingerprint()[fpid]
    fpfile = os.path.join(datadir, fpi[0]+'.npz')
    # data = np.load(fpfile) RS change
    data = np.load(fpfile, allow_pickle=True)
    fp = data['x']
    fpn = data['y']
    fpparam = fpi[1]
    # Some fingerprints are stored as bit strings
    if fpi[2] == True:
        fp = [DataStructs.CreateFromBitString(z) for z in fp]
    fpfun = fpi[3]
    data.close()
    return fp, fpn, fpparam, fpfun


def loadFingerprint3(datadir, fpid):
    fpi = fpid
    fpfile = os.path.join(datadir, fpi+'.npz')
    data = np.load(fpfile, allow_pickle=True)
    fp = data['x']
    fpn = data['y']
    fpr = data['z']
    fpd = data['d']
    data.close()

    # make it into a dictionary
    fpDict={}
    rfDist={}
    for i, r in enumerate(fpr):
        n = fpn[i]
        d = fp[i]
        dist = fpd[i]

        if r not in fpDict.keys():
            fpDict[r]={}
            rfDist[r]={}

        if n not in fpDict[r].keys():
            fpDict[r][n]={}
            rfDist[r][n]={}

        fpDict[r][n] = d
        rfDist[r][n]=  {x.split("=")[0]: x.split("=")[1] for x in dist }
    
    return fp, fpn, fpr, fpDict, rfDist




def storeReaction(smi, rfile):
    left, right = smi.split('>>')
    subs = left.split('.')
    prods = right.split('.')
    sd, pd = ({},{})
    for s in subs:
        if s not in sd:
            sd[s] = 0
        sd[s] += 1
    for p in prods:
        if p not in pd:
            pd[p] = 0
        pd[p] += 1
    rsp = {rfile: (sd, pd)}
    return rsp

def getReaction(rfile):
    rxn = rdChemReactions.ReactionFromRxnFile(rfile)
    smi = rdChemReactions.ReactionToSmiles(rxn)
    return storeReaction(smi, rfile), smi

def getReactionFromSmiles(smi, rxnfile):
    smi = '.'.join([x for x in smi.split('>>')[0].split('.') if x !='*' and x!= '[*]']) + '>>' + '.'.join([x for x in smi.split('>>')[1].split('.') if x !='*' and x!= '[*]'])
    rxn = rdChemReactions.ReactionFromSmarts(smi)
    mdl = rdChemReactions.ReactionToRxnBlock(rxn)
    with open(rxnfile, 'w') as handler:
        handler.write(mdl)
    return storeReaction(smi, rxnfile), smi

def getReactionFromSmilesFile(smartsfile, rxnfile):
    with open(smartsfile) as handler:
        smarts = handler.readline()
    rxn = rdChemReactions.ReactionFromSmarts(smarts)
    smi = rdChemReactions.ReactionToSmiles(rxn)
    mdl = rdChemReactions.ReactionToRxnBlock(rxn)
    with open(rxnfile, 'w') as handler:
        handler.write(mdl)
    return storeReaction(smi, rxnfile), smi

def getClosest(smi, fpfile, th=0.8, fp=None, fpn=None, fpp=None, fpfun=None, marvin=False):
    dist = {}
    if fp is None:
        print('Reading fingerprints')
        data = np.load(fpfile)
        fp = data['x'] 
        fpn = data['y']
        fpp = 8
        fpfun = GetMorganFingerprint
        data.close()

    targetMol = Chem.MolFromSmiles(smi)
    # If RDkit fails, we sanitize first using molconvert from ChemAxon, which is more robust
    if targetMol is None and marvin:
        try:
            cmd = ['molconvert', 'mol', smi]
            cmd2 = ['molconvert', 'smiles']
            job = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            job2 = subprocess.Popen(cmd2, stdin=job.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            job.stdout.close()
            out, err = job2.communicate()
            targetMol = Chem.MolFromSmiles(out)
        except:
            pass
    if fpp is not None:

        info1 = {}
        targetFp = AllChem.GetMorganFingerprint(targetMol, 8, bitInfo=info1, invariants=AllChem.GetConnectivityInvariants(targetMol, includeRingMembership=False))
    else:
        info1 = {}
        targetFp = AllChem.GetMorganFingerprint(targetMol, 8, bitInfo=info1, invariants=AllChem.GetConnectivityInvariants(targetMol, includeRingMembership=False))
        
    tn = DataStructs.BulkTanimotoSimilarity(targetFp, list(fp))
    for i in sorted(range(0, len(tn))):
        dist[fpn[i]] = tn[i]
    return dist, fp, fpn



def getReactants(equation):
    reactants = {}
    for x in equation.split(' + '):
        n, c = x.split(' ')
        try:
            n = int(n)
        except:
            pass
        reactants[c] = n
    return reactants

def reacSubsProds(dbfile):
    rsp = {}
    for l in open(dbfile):
        if l.startswith('#'):
            continue
        m = l.rstrip().split('\t')
        rid = m[0]
        subs = {}
        prods = {}
        m = l.rstrip().split('\t')
        left, right = m[1].split(' = ')
        subs = getReactants(left)
        prods = getReactants(right)
        ec = m[3]
        if len(subs) > 0 and len(prods) > 0:
            rsp[rid] = (subs, prods, ec)
    return rsp

def getStructs(dbfile):
    structs = {}
    for l in open(dbfile):
        if l.startswith('#'):
            continue
        m = l.rstrip().split('\t')
        cid = m[0]
        smiles = m[6]
        if len(smiles) > 0:
            structs[cid] = smiles
    return structs

def getRSim(s1, p1, s2, p2, sim):
    cl = {'s1': s1, 'p1': p1, 's2': s2, 'p2':p2}
    ss = {} 
    simm = {}
    pairs = [('s1','s2'), ('s1', 'p2'), ('p1', 's2'), ('p1', 'p2')]
    compPairs = {}
    for p in pairs:
        pairings = set()
        simm[p] = {}
        compPairs[p]=[]

        for x in cl[p[0]]:
            simm[p][x] = (0.0, x, None)
            if x in sim:
                for y in cl[p[1]]:
                    if y in sim[x]:
                        pairings.add( (sim[x][y], x, y) )

        found = {'left': set(), 'right': set()}
        for v in sorted(pairings, key = lambda h: -h[0]):
            if v[1] not in found['left'] and v[2] not in found['right']:
                # if similarity is greater that zero
                if v[0] > simm[p][v[1]][0]:
                    simm[p][v[1]] = v
                    found['left'].add(v[1])
                    found['right'].add(v[2])
                    compPairs[p].append([v[1], v[2]])
        s = []
        for x in simm[p]:
            s.append(simm[p][x][0])
        if len(s) > 0:
            ss[p] = sum(s)/len(s)
        else:
            ss[p] = 0.0
    S1 = math.sqrt(ss[pairs[0]]**2 + ss[pairs[3]]**2)/math.sqrt(2)
    S2 = math.sqrt(ss[pairs[1]]**2 + ss[pairs[2]]**2)/math.sqrt(2)

    return(S1, S2, compPairs)


def bulkTani(targetFp, fp, fpn):
    tn = DataStructs.BulkTanimotoSimilarity(targetFp, list(fp))
    dist={}
    for i in sorted(range(0, len(tn))):
        dist[fpn[i]] = tn[i]
    return dist


def generate_RFscore2(subSmiles, queryRF, queryDists, s2, r2, rfDict, rfdist, subProdPairs):  
    # subSmiles, queryRF, queryDists, s2, r2, rfDict, rfdist, subProdPairs = list(s1.keys()), queryRF, queryDists, s2, r2, rfDict, rfdist, subProdPairs[('s1', 's2')] 
    
    subList = list(subSmiles)
    
    querySubsRF = {x:queryRF[x] for x in subList if x in queryRF.keys() and len(queryRF[x])>0}
    querySubsDist = {x:queryDists[x] for x in subList if x in queryRF.keys() and len(queryDists[x])>0}
    
    dbList = list(s2.keys())
    dbSubsRF = {x:rfDict[r2][x] for x in dbList if x in rfDict[r2]}
    dbSubsDist = {x:rfdist[r2][x] for x in dbList if x in rfDict[r2]}
    
    spPairs = ["_".join([x[0], x[1]]) for x in subProdPairs]
    unweightedScores = {}
    
    for sb1, qSubRF in querySubsRF.items() :
        qSubsDist = querySubsDist[sb1]
        qSortDists = {}
        
        # iterate through the query fragments
        for k, v in qSubsDist.items():
            dists1 = [int(x[0]) for x in v]
            for d in dists1:
                if d not in qSortDists.keys():
                    qSortDists[d]=[]
                qSortDists[d].append(k)


        # iterate through the db fragments
        for sb2, dSubRF in dbSubsRF.items():
            if dSubRF =={}: 
                print('empty', sb2)
                continue
            if '_'.join([sb1, sb2]) not in spPairs:
                continue

            dSubsDist = dbSubsDist[sb2]
            dSortDists = {}
            for fragNo, k in enumerate(dSubRF.GetNonzeroElements().keys()):
                dists2 =  [int(y.split('_')[1]) for y in dSubsDist[str(k)].split('|')  ]
                for d in dists2:            
                    if d not in dSortDists.keys():
                        dSortDists[d]=[]
                    dSortDists[d].append(k)
           
            # get jaccard sim
            unweightedScores[sb1, sb2] =  {}
            
            for fragDist in set(qSortDists.keys()).union(set(qSortDists.keys())):
                if fragDist not in set(qSortDists).intersection(set(dSortDists)):
                    unweightedScores[sb1, sb2][fragDist] =0
                    
                else:
                    intersect = {frag: min([dSortDists[fragDist].count(frag), qSortDists[fragDist].count(frag)]) for frag in set(dSortDists[fragDist] + qSortDists[fragDist]) if frag in dSortDists[fragDist] and frag in qSortDists[fragDist]}
                    intersectScore = sum(intersect.values())
                    unweightedScores[sb1, sb2][fragDist] = intersectScore/len(qSortDists[fragDist])
       
    weightedScores={}
    for pair, scores in unweightedScores.items():
        weights = log_fun_weight(max(scores.keys()))
        weightedScores[pair] = sum([ scores[x]*weights[x] if x in scores and scores[x]>0 else 0 for x in list(range(0, max(scores.keys())+1)) ])

    return(weightedScores)



def log_fun_weight(c):   
    # log function 
    weights1 = []
    k = 0.75
    i = 3
    for x in list(range(0, c+1)):
        weights1.append((1 / (1 + math.e ** (k*(x - i)) ) )+0)
    return([ x/sum(weights1) for x in weights1])

def AAM_fun(subMols, prodMols, subSmiles, prodSmiles):
	# AAM using RXNmapper
	try:
	    # for unbalances reactions there need to be more atoms on the substrate side
	    if sum([x[0].GetNumAtoms() for x in subMols]) >= sum([x[0].GetNumAtoms() for x in prodMols]):
	        smile = '.'.join(subSmiles) +'>>'+'.'.join(prodSmiles)
	        reactingAtoms, conf = mcs_functions2.rxnMapper_fun(smile, subMols, prodMols, rxn_mapper)
	    else:
	        smile = '.'.join(prodSmiles) +'>>'+'.'.join(subSmiles)
	        reactingAtoms, conf = mcs_functions2.rxnMapper_fun(smile, prodMols ,subMols, rxn_mapper)  
	    return reactingAtoms, conf

	except RuntimeError: 
	    print('AAM failed query - compound too large')
	    return ([None, 0])

	except ValueError: 
	    print('AAM failed query - issue with input smiles')
	    if '*' in smile: print('please use smiles without *s')
	    return ([None, 0])

	except: 
	    print('AAM failed query')
	    return ([None, 0])

# def tidy(queryRF, prodsRF, hits1, queryAdj, prodsAdj, hits2):
#     queryRF = dict(zip(hits1, queryRF))
#     queryAdj = dict(zip(hits1, queryAdj))
#     prodsRF = dict(zip(hits2, prodsRF))
#     prodsAdj = dict(zip(hits2, prodsAdj))
#     queryRF.update(prodsRF)
#     queryAdj.update(prodsAdj)
#     return(queryRF, queryAdj)



# def draw_rfs(comp, fp, bi, rfs):
#     prints = [(comp, x, bi) for x in fp.GetNonzeroElements().keys() if x in rfs] #fp.GetOnBits()]
#     return(Draw.DrawMorganBits(prints, molsPerRow=4))
        


def run(arg, pc, rxn_mapper):

    print('in run')

    # read in the data
    if arg.out:
        fileObj = open(arg.out, 'w')    
    if arg.high:
        fileObj = open(arg.high, 'w')
    rsp = reacSubsProds(os.path.join(arg.datadir, 'reac_prop.tsv'))

    smiles = ''
    if arg.rxn is not None:
        rTarget, smiles = getReaction(arg.rxn)
    elif arg.smarts is not None:
        rxnfile = os.path.join(os.path.dirname(arg.out), 'reaction.rxn')
        try:
            rTarget, smiles = getReactionFromSmiles(arg.smarts, rxnfile)
        except:
            print('smile could not be processed')
    elif arg.smartsfile is not None:
        rxnfile = os.path.join(os.path.dirname(arg.out), 'reaction.rxn')
        rTarget, smiles = getReactionFromSmilesFile(arg.smartsfile, rxnfile)        
    elif arg.rid is not None:
        struct = getStructs(arg.chem)
        rTarget = {arg.rid: [{},{}]}
        for side in (0,1):
            for s in rsp[arg.rid][side]:
                if s in struct:
                    rTarget[arg.rid][side][struct[s]] = rsp[arg.rid][side][s]
    else:
        raise Exception('No target')
    
        
    
    # Read fingerprint info from preload data if available
    if pc is not None: 
        if arg.fp in pc.fp:
            fp, fpn, fpp, fpfun = pc.fp[arg.fp]
            fpRF, fpnRF, fprRF, rfDict, rfdist = pc.fpr[arg.fp]
        else:
            fp, fpn, fpp, fpfun = loadFingerprint(arg.datadir, arg.fp)
            fpRF, fpnRF, fprRF, rfDict, rfdist = loadFingerprint3(arg.datadir, 'FP_MorgRF')     
    else:      
        print('reading fp data')
        fp, fpn, fpp, fpfun = loadFingerprint(arg.datadir, arg.fp)
        fpRF, fpnRF, fprRF, rfDict, rfdist = loadFingerprint3(arg.datadir, 'FP_MorgRF')
  
    
    
    queryRF = {}
    queryDists = {}
    sim={}
    
    # for the input query reactions, do AAM
    # then iterate through the query reaction compounds and 
        # calculate distance to compound database (whole compounds)
        # get RFs        
    
    for r in rTarget:        
        print('\nAAM of the Query reaction') 
        subSmiles = rTarget[r][0].keys()
        prodSmiles = rTarget[r][1].keys()
        if set(subSmiles) == set(prodSmiles):
            print('no transformation')
            
        #comp, atomMap, fpM, info, fragAtoms2, smile, count
        subMols = [process_compF(k, 8) +(k, v,) for k, v in rTarget[r][0].items()]
        prodMols = [process_compF(k, 8) +(k, v,) for k, v in rTarget[r][1].items()]
    
        # AAM using RXNmapper
        reactingAtoms, conf = AAM_fun(subMols, prodMols, subSmiles, prodSmiles)        
 
        # measure compound similarities
        print('\nCompound-compound distances')
        for comp in subMols + prodMols:
            smile = comp[5]
            # measure distances for whole compounds - equivalent to getClosest
            sim[smile] = bulkTani(comp[2], fp, fpn) 
            
            # measure distances for compound fragments
            if conf>0 and smile in reactingAtoms:
                # rfs are fragNumber:(startAtom, dist), dists are fragNumber: distFromRA, startAtom, RA                
                rfs, dists = reactFragDists(comp, reactingAtoms[smile])  
                
                if len(rfs)>0:
                    queryRF[smile]=rfs
                    queryDists[smile]=dists  
                    # draw_rfs(comp[0], comp[2], comp[3], rfs)

                           
    # Get reaction similarities
    for r1 in rTarget:
        s1, p1 = rTarget[r1]      
        for r2 in rsp: 
            ### whole compound similarity                        
            s2, p2, ec2 = rsp[r2]   
            if s2 == p2: continue
            S1, S2, subProdPairs = getRSim(s1, p1, s2, p2, sim)
            if S1 > 0 and S2 > 0:
            
                # if aam failed, record scores replacing these values with Nan
                if conf>0 or r2 not in rfDict.keys():
                    if arg.out:
                       print(r1, r2, S1, S2, smiles,  float("Nan"), ec2, file = fileObj)
                       
                    if arg.high:
                        print(r1, r2, max([S1, S2]),  smiles,  float("Nan"), ec2, file = fileObj) 
                    continue
                

                ### RF similarity
                RF_score=float("Nan")

                subProdPairs = {k:[x for x in v if x[0] in queryRF.keys()]  for k, v in subProdPairs.items()}
                try:
                    # calculate the scores for the RFs
                    # forward score
                    if S1 >= S2:
                        S_RF = generate_RFscore2(list(s1.keys()), queryRF, queryDists, s2, r2, rfDict, rfdist, subProdPairs[('s1', 's2')] )
                        P_RF = generate_RFscore2(list(p1.keys()), queryRF, queryDists, p2, r2, rfDict, rfdist, subProdPairs[('p1', 'p2')] )
                        if (sum(S_RF.values())+sum(P_RF.values()))>0: 
                            RF_score = (sum(S_RF.values())+sum(P_RF.values())) / len(queryRF) #(len(S_RF) + len(P_RF))
                        else: RF_score=0
                    else:
                        # reverse score
                        S_RF = generate_RFscore2(list(s1.keys()), queryRF, queryDists, p2, r2, rfDict, rfdist, subProdPairs[('s1', 'p2')])
                        P_RF = generate_RFscore2(list(p1.keys()), queryRF, queryDists, s2, r2, rfDict, rfdist, subProdPairs[('p1', 's2')])
                        if (sum(S_RF.values())+sum(P_RF.values()))>0: 
                            # geometric mean 
                            RF_score = math.sqrt(mean(S_RF.values()) * mean(P_RF.values()))
                        else: RF_score=0
                except:
                    RF_score = float("Nan")
                
                if arg.out:
                    print(r1, r2, S1, S2, smiles, RF_score, ec2,   file = fileObj) 

                if arg.high:
                    if S1 >= S2:
                        print(r1, r2, S1, smiles,  RF_score, ec2,  file = fileObj)
                    else:
                        print(r1, r2, S2, smiles,  RF_score, ec2,   file = fileObj)                





 
def arguments(args=None):
    parser = argparse.ArgumentParser(description='quickRSim Pablo Carbonell, SYNBIOCHEM, 2016')
    parser.add_argument('datadir', help='Data folder')
    parser.add_argument('fp', help='Fingerprint for reactants')
    parser.add_argument('-fpr', help='Fingerprint for reactants', default='FP_MorgRF')
    parser.add_argument('-rxn', 
                        help='Input reaction rxn file')
    parser.add_argument('-rid', 
                        help='Input reaction id')
    parser.add_argument('-smarts', 
                        help='Input reaction SMARTS')
    parser.add_argument('-smartsfile', 
                        help='Input reaction SMARTS file')
    parser.add_argument('-chem', 
                        help='Metanetx chemical structures (if input is reaction id)')
    parser.add_argument('-th', type=float, default=0.8, 
                        help='Similarity threshold [default=0.8]')
    parser.add_argument('-out', 
                        help='Output results in .txt file, please specify file name')
    parser.add_argument('-high', 
                        help='Output results in .txt file with highest similarity score from both forwards and backwards reactions, please specify file name')
    parser.add_argument('-marvin', 
                        help='Call marvin if needed (skip if fails)')

    if args is not None:
        arg = parser.parse_args(args=args)
    else:
        arg = parser.parse_args()
    return arg      



if __name__ == '__main__':
    arg = arguments()

    # smi = 'C[C@]12CC[C@H]3[C@@H](CCC4=CC(=O)CC[C@@]43C)[C@@H]1CC[C@]2(O)C(=O)CO>>C[C@]12C[C@H](O)[C@H]3[C@@H](CCC4=CC(=O)CC[C@@]43C)[C@@H]1CC[C@]2(O)C(=O)CO'    
    # fp = '/home/ruth/code/update_selenzyme/selenzyme_2023/selenzyme2/selenzyPro/data/'
    # arg = arguments([fp, 
    #     'Morgan',
    #     '-smarts', smi, 
    #     '-out', '/home/ruth/code/update_selenzyme/selenzyme_2023/selenzyme2/selenzyPro/uploads/RSquickRsim_new.txt'] )
    # pc=None
    
    
    rxn_mapper = RXNMapper()     
    run(arg, pc, rxn_mapper)

 
 

