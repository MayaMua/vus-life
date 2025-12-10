import hgvs.dataproviders.uta
import hgvs.parser
from bioutils.seqfetcher import fetch_seq
import pandas as pd

# 初始化连接
hdp = hgvs.dataproviders.uta.connect()
parser = hgvs.parser.Parser()

def get_reference_base(ac, pos):
    """获取指定位置的一个参考碱基 (1-based index)"""
    try:
        # bioutils 使用 0-based，区间是 [start, end)
        return fetch_seq(ac, start_i=pos - 1, end_i=pos)
    except Exception as e:
        print(f"Error fetching base: {e}")
        return "N"

def hgvs_g_to_vcf(hgvs_g_str):
    if not hgvs_g_str or pd.isna(hgvs_g_str):
        return None
    
    try:
        var_g = parser.parse_hgvs_variant(hgvs_g_str)
        ac = var_g.ac
        pos_hgvs = var_g.posedit.pos
        edit = var_g.posedit.edit
        
        chrom = ac.split('.')[0].replace('NC_0000', '')
        
        # --- 情况 A: Dup (重复) ---
        # 逻辑：获取被重复的序列，将其视为在这个区间末尾的“插入”
        if edit.type == 'dup':
            # 1. 确定重复的范围
            start = pos_hgvs.start.base
            end = pos_hgvs.end.base
            
            # 2. 从参考基因组抓取被重复的序列
            duplicated_seq = fetch_seq(ac, start_i=start-1, end_i=end)
            
            # 3. 构建 VCF (右对齐逻辑，锚定在重复区间的最后一个碱基)
            pos_vcf = end
            ref = get_reference_base(ac, pos_vcf)
            alt = ref + duplicated_seq
            
        # --- 情况 B: Ins (插入) ---
        elif edit.type == 'ins':
            pos_vcf = pos_hgvs.start.base
            ref = get_reference_base(ac, pos_vcf)
            alt = ref + edit.alt
            
        # --- 情况 C: Del (缺失) ---
        elif edit.type == 'del':
            # VCF 缺失通常需要前一个碱基作为锚点
            start = pos_hgvs.start.base
            end = pos_hgvs.end.base
            
            # 锚点设在缺失开始前的一个碱基
            pos_vcf = start - 1 
            anchor_base = get_reference_base(ac, pos_vcf)
            
            # 获取被删除的序列
            deleted_seq = fetch_seq(ac, start_i=start-1, end_i=end)
            
            ref = anchor_base + deleted_seq # VCF REF: 锚点 + 被删序列
            alt = anchor_base               # VCF ALT: 仅剩锚点
            
        # --- 情况 D: Sub (替换) ---
        elif edit.type == 'sub':
            pos_vcf = pos_hgvs.start.base
            ref = edit.ref
            alt = edit.alt
            
        else:
            print(f"Unsupported type: {edit.type}")
            return None

        return {
            "chrom": int(chrom),
            "pos": int(pos_vcf),
            "ref": ref,
            "alt": alt
        }

    except Exception as e:
        print(f"Error converting {hgvs_g_str}: {e}")
        return None

if __name__ == "__main__":
    # 测试
    hgvs_list = [
        "NC_000015.10:g.48487139dup",       # 你的报错案例 (Dup)
        "NC_000016.10:g.23607966_23607967insA", # 之前的案例 (Ins)
        "NC_000015.10:g.48644723del"
    ]

    for g in hgvs_list:
        print(f"Input: {g}")
        print(f"Result: {hgvs_g_to_vcf(g)}\n")