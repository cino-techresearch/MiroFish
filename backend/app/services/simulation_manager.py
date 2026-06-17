"""
OASIS Simulation Manager
Manages parallel simulation across Twitter and Reddit platforms
Uses preset scripts + LLM-based intelligent configuration parameter generation
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.logger import get_logger
from .zep_entity_reader import ZepEntityReader, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .profile_source import FileProfileSource, GeneratedProfileSource
from .injection_consistency import validate_injection_consistency, InjectionConsistencyError
from .simulation_config_generator import SimulationConfigGenerator, SimulationParameters
from ..models.project import ProjectManager
from ..utils.locale import t

logger = get_logger('mirofish.simulation')


class SimulationStatus(str, Enum):
    """Simulation status"""
    CREATED = "created"
    PREPARING = "preparing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"      # Simulation manually stopped
    COMPLETED = "completed"  # Simulation completed naturally
    FAILED = "failed"


class PlatformType(str, Enum):
    """Platform type"""
    TWITTER = "twitter"
    REDDIT = "reddit"


@dataclass
class SimulationState:
    """Simulation state"""
    simulation_id: str
    project_id: str
    graph_id: str

    # Platform enable flags
    enable_twitter: bool = True
    enable_reddit: bool = True

    # Status
    status: SimulationStatus = SimulationStatus.CREATED

    # Preparation phase data
    entities_count: int = 0
    profiles_count: int = 0
    entity_types: List[str] = field(default_factory=list)

    # Config generation info
    config_generated: bool = False
    config_reasoning: str = ""

    # Runtime data
    current_round: int = 0
    twitter_status: str = "not_started"
    reddit_status: str = "not_started"

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Error info
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Full state dictionary (internal use)"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "enable_twitter": self.enable_twitter,
            "enable_reddit": self.enable_reddit,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "config_reasoning": self.config_reasoning,
            "current_round": self.current_round,
            "twitter_status": self.twitter_status,
            "reddit_status": self.reddit_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }
    
    def to_simple_dict(self) -> Dict[str, Any]:
        """Simplified state dictionary (for API responses)"""
        return {
            "simulation_id": self.simulation_id,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "entities_count": self.entities_count,
            "profiles_count": self.profiles_count,
            "entity_types": self.entity_types,
            "config_generated": self.config_generated,
            "error": self.error,
        }


class SimulationManager:
    """
    Simulation Manager

    Core responsibilities:
    1. Read and filter entities from the Zep graph
    2. Generate OASIS Agent Profiles
    3. Intelligently generate simulation configuration parameters using LLM
    4. Prepare all files required by the preset scripts
    """

    # Simulation data storage directory
    SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), 
        '../../uploads/simulations'
    )
    
    def __init__(self):
        # Ensure the directory exists
        os.makedirs(self.SIMULATION_DATA_DIR, exist_ok=True)

        # In-memory simulation state cache
        self._simulations: Dict[str, SimulationState] = {}
    
    def _get_simulation_dir(self, simulation_id: str) -> str:
        """Get the simulation data directory"""
        sim_dir = os.path.join(self.SIMULATION_DATA_DIR, simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        return sim_dir
    
    def _save_simulation_state(self, state: SimulationState):
        """Save simulation state to file"""
        sim_dir = self._get_simulation_dir(state.simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        state.updated_at = datetime.now().isoformat()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        
        self._simulations[state.simulation_id] = state
    
    def _load_simulation_state(self, simulation_id: str) -> Optional[SimulationState]:
        """Load simulation state from file"""
        if simulation_id in self._simulations:
            return self._simulations[simulation_id]
        
        sim_dir = self._get_simulation_dir(simulation_id)
        state_file = os.path.join(sim_dir, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=data.get("project_id", ""),
            graph_id=data.get("graph_id", ""),
            enable_twitter=data.get("enable_twitter", True),
            enable_reddit=data.get("enable_reddit", True),
            status=SimulationStatus(data.get("status", "created")),
            entities_count=data.get("entities_count", 0),
            profiles_count=data.get("profiles_count", 0),
            entity_types=data.get("entity_types", []),
            config_generated=data.get("config_generated", False),
            config_reasoning=data.get("config_reasoning", ""),
            current_round=data.get("current_round", 0),
            twitter_status=data.get("twitter_status", "not_started"),
            reddit_status=data.get("reddit_status", "not_started"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            error=data.get("error"),
        )
        
        self._simulations[simulation_id] = state
        return state
    
    def create_simulation(
        self,
        project_id: str,
        graph_id: str,
        enable_twitter: bool = True,
        enable_reddit: bool = True,
    ) -> SimulationState:
        """
        Create a new simulation.

        Args:
            project_id: Project ID
            graph_id: Zep graph ID
            enable_twitter: Whether to enable Twitter simulation
            enable_reddit: Whether to enable Reddit simulation

        Returns:
            SimulationState
        """
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"
        
        state = SimulationState(
            simulation_id=simulation_id,
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=enable_twitter,
            enable_reddit=enable_reddit,
            status=SimulationStatus.CREATED,
        )
        
        self._save_simulation_state(state)
        logger.info(f"Simulation created: {simulation_id}, project={project_id}, graph={graph_id}")
        
        return state
    
    def prepare_simulation(
        self,
        simulation_id: str,
        simulation_requirement: str,
        document_text: str,
        defined_entity_types: Optional[List[str]] = None,
        use_llm_for_profiles: bool = True,
        progress_callback: Optional[callable] = None,
        parallel_profile_count: int = 3
    ) -> SimulationState:
        """
        Prepare the simulation environment (fully automated).

        Steps:
        1. Read and filter entities from the Zep graph
        2. Generate OASIS Agent Profiles for each entity (optional LLM enhancement, supports parallel)
        3. Intelligently generate simulation configuration parameters using LLM (time, activity, post frequency, etc.)
        4. Save configuration files and profile files
        5. Copy preset scripts to the simulation directory

        Args:
            simulation_id: Simulation ID
            simulation_requirement: Simulation requirement description (used for LLM config generation)
            document_text: Original document content (used for LLM background understanding)
            defined_entity_types: Predefined entity types (optional)
            use_llm_for_profiles: Whether to use LLM to generate detailed personas
            progress_callback: Progress callback function (stage, progress, message)
            parallel_profile_count: Number of profiles to generate in parallel, default 3

        Returns:
            SimulationState
        """
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"Simulation not found: {simulation_id}")

        try:
            state.status = SimulationStatus.PREPARING
            self._save_simulation_state(state)
            
            sim_dir = self._get_simulation_dir(simulation_id)
            
            # ========== Phase 1: Read and filter entities ==========
            if progress_callback:
                progress_callback("reading", 0, t('progress.connectingZepGraph'))
            
            reader = ZepEntityReader()
            
            if progress_callback:
                progress_callback("reading", 30, t('progress.readingNodeData'))
            
            filtered = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=defined_entity_types,
                enrich_with_edges=True
            )
            
            state.entities_count = filtered.filtered_count
            state.entity_types = list(filtered.entity_types)
            
            if progress_callback:
                progress_callback(
                    "reading", 100,
                    t('progress.readingComplete', count=filtered.filtered_count),
                    current=filtered.filtered_count,
                    total=filtered.filtered_count
                )
            
            # 주입 프로필 경로 여부를 엔티티-0 가드보다 먼저 판정한다 (FR-005).
            # 주입 경로는 엔티티-0이어도 generic "엔티티 없음" 으로 선점되지 않고,
            # 아래 cheap pre-check(프로필 수 != 엔티티 수)가 더 명확한 사유로 처리한다.
            injected_profiles_path = os.path.join(sim_dir, "injected_profiles.json")
            is_injected_profiles = os.path.exists(injected_profiles_path)

            if filtered.filtered_count == 0 and not is_injected_profiles:
                state.status = SimulationStatus.FAILED
                state.error = "No matching entities found; please verify the graph has been built correctly"
                self._save_simulation_state(state)
                return state

            # ========== Phase 2: Generate Agent Profiles ==========
            total_entities = len(filtered.entities)
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 0,
                    t('progress.startGenerating'),
                    current=0,
                    total=total_entities
                )
            
            def profile_progress(current, total, msg):
                if progress_callback:
                    progress_callback(
                        "generating_profiles",
                        int(current / total * 100),
                        msg,
                        current=current,
                        total=total,
                        item_name=msg
                    )

            # ProfileSource 분기 (FR-005, FR-011):
            # injected_profiles.json 이 있으면 주입 프로필을 로드(LLM 0회)하고 생성을 건너뛴다.
            # 그 외에는 현행 ZEP 엔티티 기반 생성 경로를 사용한다.
            if is_injected_profiles:
                profiles = FileProfileSource(profiles_path=injected_profiles_path).load_profiles()
                # OASIS 정합(FR-005): OASIS 는 agent_id 를 프로필 *위치*(0..N-1)로 부여한다.
                # 임의 개수 주입은 허용하되, user_id 를 위치 인덱스로 정규화해 agent_id/
                # 저장 user_id/poster_agent_id 가 모두 OASIS 위치와 일치하게 한다.
                for idx, p in enumerate(profiles):
                    p.user_id = idx
                # 저장은 LLM 키 없이 가능한 serializer 만 사용 (generator __init__ 우회)
                saver = OasisProfileGenerator.__new__(OasisProfileGenerator)
            else:
                # Pass graph_id to enable Zep retrieval and obtain richer context
                generator = OasisProfileGenerator(graph_id=state.graph_id)

                # Set the real-time save file path (prefer Reddit JSON format)
                realtime_output_path = None
                realtime_platform = "reddit"
                if state.enable_reddit:
                    realtime_output_path = os.path.join(sim_dir, "reddit_profiles.json")
                    realtime_platform = "reddit"
                elif state.enable_twitter:
                    realtime_output_path = os.path.join(sim_dir, "twitter_profiles.csv")
                    realtime_platform = "twitter"

                # GeneratedProfileSource 어댑터를 통해 생성 (생성 경로도 ProfileSource 추상 사용)
                gen_source = GeneratedProfileSource(
                    entities=filtered.entities,
                    use_llm=use_llm_for_profiles,
                    progress_callback=profile_progress,
                    graph_id=state.graph_id,
                    parallel_count=parallel_profile_count,
                    realtime_output_path=realtime_output_path,
                    output_platform=realtime_platform,
                    generator=generator,
                )
                profiles = gen_source.load_profiles()
                saver = generator

            state.profiles_count = len(profiles)

            # FR-009: profile layer provenance 기록 (주입=file / 생성=generated)
            try:
                _proj = ProjectManager.get_project(state.project_id)
                if _proj is not None:
                    _proj.profile_source = "file" if is_injected_profiles else "generated"
                    ProjectManager.save_project(_proj)
            except Exception as _e:
                logger.warning(f"profile_source provenance 기록 실패: {_e}")

            # FR-005 재설계: 주입 프로필은 임의 개수 허용 — agent_config 를 프로필에서 파생하므로
            # ZEP 엔티티 수와의 일치 요구를 제거한다(아래 generate_config 에 agent_profiles 전달).

            # Save profile files (note: Twitter uses CSV format, Reddit uses JSON format)
            # Reddit has already been saved in real time during generation; save again here to ensure completeness
            if progress_callback:
                progress_callback(
                    "generating_profiles", 95,
                    t('progress.savingProfiles'),
                    current=total_entities,
                    total=total_entities
                )
            
            if state.enable_reddit:
                saver.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "reddit_profiles.json"),
                    platform="reddit"
                )

            if state.enable_twitter:
                # Twitter uses CSV format — this is an OASIS requirement
                saver.save_profiles(
                    profiles=profiles,
                    file_path=os.path.join(sim_dir, "twitter_profiles.csv"),
                    platform="twitter"
                )
            
            if progress_callback:
                progress_callback(
                    "generating_profiles", 100,
                    t('progress.profilesComplete', count=len(profiles)),
                    current=len(profiles),
                    total=len(profiles)
                )
            
            # ========== Phase 3: Intelligently generate simulation config using LLM ==========
            if progress_callback:
                progress_callback(
                    "generating_config", 0,
                    t('progress.analyzingRequirements'),
                    current=0,
                    total=3
                )
            
            config_generator = SimulationConfigGenerator()
            
            if progress_callback:
                progress_callback(
                    "generating_config", 30,
                    t('progress.callingLLMConfig'),
                    current=1,
                    total=3
                )
            
            sim_params = config_generator.generate_config(
                simulation_id=simulation_id,
                project_id=state.project_id,
                graph_id=state.graph_id,
                simulation_requirement=simulation_requirement,
                document_text=document_text,
                entities=filtered.entities,
                enable_twitter=state.enable_twitter,
                enable_reddit=state.enable_reddit,
                # FR-005 재설계: 주입 프로필이면 agent_config 를 프로필에서 파생(엔티티 수 무관)
                agent_profiles=profiles if is_injected_profiles else None,
            )
            
            if progress_callback:
                progress_callback(
                    "generating_config", 70,
                    t('progress.savingConfigFiles'),
                    current=2,
                    total=3
                )
            
            # Save configuration file
            config_path = os.path.join(sim_dir, "simulation_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(sim_params.to_json())
            
            state.config_generated = True
            state.config_reasoning = sim_params.generation_reasoning

            # FR-012: 프로필 주입 경로면 주입 프로필 ↔ agent_configs ↔ initial_posts 정합성 fail-fast
            if os.path.exists(injected_profiles_path):
                event_config = getattr(sim_params, "event_config", None)
                initial_posts = getattr(event_config, "initial_posts", []) if event_config else []
                try:
                    validate_injection_consistency(
                        profiles,
                        getattr(sim_params, "agent_configs", []),
                        initial_posts,
                    )
                except InjectionConsistencyError as ce:
                    # 부분 산출물 정리: config_generated 를 내리고 생성된 산출물(config + 프로필 파일) 제거.
                    # (이렇게 해야 _check_simulation_prepared 가 이 FAILED 를 "준비됨"으로 오판하지 않음)
                    state.config_generated = False
                    for _stale in (config_path,
                                   os.path.join(sim_dir, "reddit_profiles.json"),
                                   os.path.join(sim_dir, "twitter_profiles.csv")):
                        try:
                            if os.path.exists(_stale):
                                os.remove(_stale)
                        except OSError:
                            pass
                    state.status = SimulationStatus.FAILED
                    state.error = str(ce)
                    self._save_simulation_state(state)
                    return state

            if progress_callback:
                progress_callback(
                    "generating_config", 100,
                    t('progress.configComplete'),
                    current=3,
                    total=3
                )
            
            # Note: run scripts remain in the backend/scripts/ directory and are no longer copied to the simulation directory.
            # When starting the simulation, simulation_runner will run scripts from the scripts/ directory.

            # Update status
            state.status = SimulationStatus.READY
            self._save_simulation_state(state)
            
            logger.info(f"Simulation preparation complete: {simulation_id}, "
                       f"entities={state.entities_count}, profiles={state.profiles_count}")
            
            return state
            
        except Exception as e:
            logger.error(f"Simulation preparation failed: {simulation_id}, error={str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            state.status = SimulationStatus.FAILED
            state.error = str(e)
            self._save_simulation_state(state)
            raise
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """Get simulation state"""
        return self._load_simulation_state(simulation_id)
    
    def list_simulations(self, project_id: Optional[str] = None) -> List[SimulationState]:
        """List all simulations"""
        simulations = []
        
        if os.path.exists(self.SIMULATION_DATA_DIR):
            for sim_id in os.listdir(self.SIMULATION_DATA_DIR):
                # Skip hidden files (e.g. .DS_Store) and non-directory entries
                sim_path = os.path.join(self.SIMULATION_DATA_DIR, sim_id)
                if sim_id.startswith('.') or not os.path.isdir(sim_path):
                    continue
                
                state = self._load_simulation_state(sim_id)
                if state:
                    if project_id is None or state.project_id == project_id:
                        simulations.append(state)
        
        return simulations
    
    def get_profiles(self, simulation_id: str, platform: str = "reddit") -> List[Dict[str, Any]]:
        """Get Agent Profiles for the simulation"""
        state = self._load_simulation_state(simulation_id)
        if not state:
            raise ValueError(f"Simulation not found: {simulation_id}")
        
        sim_dir = self._get_simulation_dir(simulation_id)
        profile_path = os.path.join(sim_dir, f"{platform}_profiles.json")
        
        if not os.path.exists(profile_path):
            return []
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_simulation_config(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get simulation configuration"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_run_instructions(self, simulation_id: str) -> Dict[str, str]:
        """Get run instructions"""
        sim_dir = self._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        return {
            "simulation_dir": sim_dir,
            "scripts_dir": scripts_dir,
            "config_file": config_path,
            "commands": {
                "twitter": f"python {scripts_dir}/run_twitter_simulation.py --config {config_path}",
                "reddit": f"python {scripts_dir}/run_reddit_simulation.py --config {config_path}",
                "parallel": f"python {scripts_dir}/run_parallel_simulation.py --config {config_path}",
            },
            "instructions": (
                f"1. Activate conda environment: conda activate MiroFish\n"
                f"2. Run simulation (scripts located in {scripts_dir}):\n"
                f"   - Twitter only: python {scripts_dir}/run_twitter_simulation.py --config {config_path}\n"
                f"   - Reddit only: python {scripts_dir}/run_reddit_simulation.py --config {config_path}\n"
                f"   - Both platforms in parallel: python {scripts_dir}/run_parallel_simulation.py --config {config_path}"
            )
        }
