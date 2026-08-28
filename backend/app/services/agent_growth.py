from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


class AgentEvolutionStage:
    NOVICE = "🌱 Yenidoğan"       # Level 1: 0 - 100 XP
    APPRENTICE = "🌿 Çırak"       # Level 2: 101 - 400 XP
    SPECIALIST = "🎓 Uzman"       # Level 3: 401 - 1000 XP
    MASTER = "👑 Üstat (Master)"  # Level 4: 1001+ XP


class AgentGrowthEngine:
    """
    'Living & Evolving Agent' IQ & Growth Progression Engine.
    
    1. Tracks XP points, Level (1 -> 4), and Evolution Stage.
    2. Calculates Dynamic IQ score based on runs, accuracy, memory facts, and tools mastered.
    3. Records milestone achievements into agent's growth history timeline.
    """

    XP_LEVEL_THRESHOLDS = [
        (1, 0, 100, AgentEvolutionStage.NOVICE, "Temel sistem rolüyle öğrenmeye başladı."),
        (2, 101, 400, AgentEvolutionStage.APPRENTICE, "Kullanıcı tercihlerini ve temel çalışma kalıplarını öğrendi."),
        (3, 401, 1000, AgentEvolutionStage.SPECIALIST, "Canlı web ve API kaynaklarını kusursuz analiz ediyor, ReAct muhakemesi gelişti."),
        (4, 1001, 999999, AgentEvolutionStage.MASTER, "En yüksek sezgisel hafıza ve otonom problem çözme zekasına ulaştı.")
    ]

    # XP Reward Constants
    XP_REWARD_RUN_TASK = 20
    XP_REWARD_WEB_API_DATA = 30
    XP_REWARD_NEW_MEMORY_FACT = 15
    XP_REWARD_USER_UPVOTE = 50
    XP_REWARD_KNOWLEDGE_SOURCE_ADDED = 40

    @classmethod
    def calculate_level_and_stage(cls, current_xp: int) -> Tuple[int, str, int, int, float]:
        """
        Calculates (level, stage_title, current_level_min_xp, next_level_xp, progress_percentage).
        """
        for lvl, min_xp, max_xp, stage_title, _ in cls.XP_LEVEL_THRESHOLDS:
            if min_xp <= current_xp <= max_xp:
                total_in_level = max_xp - min_xp
                gained_in_level = current_xp - min_xp
                progress_pct = round((gained_in_level / total_in_level) * 100, 1) if total_in_level > 0 else 100.0
                return lvl, stage_title, min_xp, max_xp, min(100.0, max(0.0, progress_pct))

        return 4, AgentEvolutionStage.MASTER, 1000, 1000, 100.0

    @classmethod
    def calculate_iq_score(cls, total_runs: int, memory_fact_count: int, knowledge_source_count: int, level: int) -> int:
        """
        Calculates dynamic Intelligence Quotient (IQ) score (Base: 80, Max: 180+).
        """
        base_iq = 85
        run_bonus = min(30, total_runs * 2)
        fact_bonus = min(35, memory_fact_count * 3)
        knowledge_bonus = min(25, knowledge_source_count * 5)
        level_bonus = level * 10
        
        return base_iq + run_bonus + fact_bonus + knowledge_bonus + level_bonus

    @classmethod
    def award_xp(
        cls,
        current_xp: int,
        xp_gain: int,
        reason: str,
        growth_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Awards XP to the agent, checks for level up, and returns updated growth status.
        """
        old_level, old_stage, _, _, _ = cls.calculate_level_and_stage(current_xp)
        new_xp = current_xp + xp_gain
        new_level, new_stage, min_xp, max_xp, progress_pct = cls.calculate_level_and_stage(new_xp)

        history = list(growth_history or [])
        leveled_up = new_level > old_level

        if leveled_up:
            history.append({
                "type": "LEVEL_UP",
                "level": new_level,
                "stage": new_stage,
                "date": datetime.now(timezone.utc).isoformat(),
                "description": f"Tebrikler! Bot {new_stage} seviyesine ulaştı ({new_xp} XP)."
            })
        elif xp_gain >= 30:
            history.append({
                "type": "MILESTONE",
                "xp_gained": xp_gain,
                "reason": reason,
                "date": datetime.now(timezone.utc).isoformat()
            })

        return {
            "new_xp": new_xp,
            "level": new_level,
            "stage": new_stage,
            "progress_pct": progress_pct,
            "leveled_up": leveled_up,
            "growth_history": history[-20:]
        }
