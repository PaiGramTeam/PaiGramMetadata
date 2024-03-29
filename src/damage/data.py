import json
from typing import Dict, Any

from .artifact import artifact
from .character import character
from .models import CharacterDamage, CharacterConfig, WeaponConfig
from .skill_data import SkillData
from .weapon import weapon


class Data:
    def __init__(self):
        self.file_name = "GenshinDamageRule.json"
        self.file_data: Dict[str, CharacterDamage] = self.load()
        self.patch_character()
        self.add_new_default_config()

    def load(self) -> Dict[str, CharacterDamage]:
        with open(self.file_name, "r", encoding="utf-8") as f:
            _data = json.load(f)
        new_data = {}
        for k, v in _data.items():
            new_data[k] = CharacterDamage(**v)
        return new_data

    def patch_character(self):
        for c_name, v in self.file_data.items():
            custom_name_map = {}
            damage_key_map = {}
            transformative_damage_key_map = {}
            for skill in v.skills:
                custom_name_map[skill.index] = skill.name
                damage_key_map[skill.index] = skill.damage_key
                transformative_damage_key_map[
                    skill.index
                ] = skill.transformative_damage_key
            for skill in character.skills_map[c_name]:
                if skill.index in custom_name_map:
                    skill.custom_name = custom_name_map[skill.index]
                    skill.damage_key = damage_key_map[skill.index]
                    skill.transformative_damage_key = transformative_damage_key_map[
                        skill.index
                    ]

    def add_new_default_config(self):
        # 版本更新时，自动添加新的默认配置。只处理 config_weapon artifact_config
        self.add_new_default_config_weapon()
        self.add_new_default_config_artifact()

    def add_new_default_config_weapon(self):
        for c_name, v in self.file_data.items():
            if v.config_weapon:
                for w_name, w_value in v.config_weapon.items():
                    w = weapon.get_by_name(w_name)
                    if not w:
                        continue
                    for config in w.config:
                        if config.name not in w_value:
                            w_value[config.name] = config.default

    def add_new_default_config_artifact(self):
        for c_name, v in self.file_data.items():
            if v.artifact_config:
                for a_name, a_value in v.artifact_config.items():
                    a = artifact.get_by_name(a_name)
                    if not a:
                        continue
                    for config in a.config:
                        if config.name not in a_value:
                            a_value[config.name] = config.default

    def dump(self) -> Dict[str, Dict]:
        new_data = {}
        for k, v in self.file_data.items():
            new_data[k] = v.dict()
        return new_data

    def save(self):
        with open(self.file_name, "w", encoding="utf-8") as f:
            json.dump(self.dump(), f, ensure_ascii=False, indent=4)

    def first_init(self, character_name: str):
        if character_name in self.file_data:
            return
        self.file_data[character_name] = CharacterDamage(skills=[])

    def last_close(self, character_name: str):
        if character_name not in self.file_data:
            return
        data_ = self.file_data[character_name]

        def last_close_weapon_or_artifact():
            if data_.config_weapon:
                for k, v in data_.config_weapon.copy().items():
                    if not v:
                        del data_.config_weapon[k]
            if data_.artifact_config:
                for k, v in data_.artifact_config.copy().items():
                    if not v:
                        del data_.artifact_config[k]

        def last_close_skills():
            if data_.skills:
                for v in data_.skills.copy():
                    if not v.damage_key and not v.transformative_damage_key:
                        data_.skills.remove(v)

        last_close_skills()
        last_close_weapon_or_artifact()
        if len(data_.skills) != 0:
            return
        if data_.config is not None and data_.config:
            return
        if data_.config_skill is not None and data_.config_skill:
            return
        if data_.config_weapon is not None and data_.config_weapon:
            return
        if data_.artifact_config is not None and data_.artifact_config:
            return
        del self.file_data[character_name]

    def get_character_config_value(
        self, character_name: str, config_: CharacterConfig
    ) -> Any:
        if not self.file_data.get(character_name):
            return None
        if not self.file_data[character_name].config:
            return None
        return self.file_data[character_name].config.get(config_.name, None)

    def set_character_config_value(
        self, character_name: str, config: CharacterConfig, value: Any
    ):
        self.first_init(character_name)
        if not self.file_data[character_name].config:
            self.file_data[character_name].config = {}
        if isinstance(config.default, bool):
            new_value = value == "true"
        else:
            value_class = type(config.default)
            new_value = value_class(value)
        self.file_data[character_name].config[config.name] = new_value
        self.last_close(character_name)

    def get_character_skill_config_value(
        self, character_name: str, config_: CharacterConfig
    ) -> Any:
        if not self.file_data.get(character_name):
            return None
        if not self.file_data[character_name].config_skill:
            return None
        return self.file_data[character_name].config_skill.get(config_.name, None)

    def set_character_skill_config_value(
        self, character_name: str, config: CharacterConfig, value: Any
    ):
        self.first_init(character_name)
        if not self.file_data[character_name].config_skill:
            self.file_data[character_name].config_skill = {}
        if isinstance(config.default, bool):
            new_value = value == "true"
        else:
            value_class = type(config.default)
            new_value = value_class(value)
        self.file_data[character_name].config_skill[config.name] = new_value
        self.last_close(character_name)

    def get_character_weapon_config_value(
        self, character_name: str, config_: WeaponConfig
    ) -> Any:
        if not self.file_data.get(character_name):
            return None
        if not self.file_data[character_name].config_weapon:
            return None
        data_ = self.file_data[character_name].config_weapon.get(config_.parent, None)
        if not data_:
            return None
        return data_.get(config_.name, None)

    def set_character_weapon_config_value(
        self, character_name: str, config: WeaponConfig, value: Any
    ):
        self.first_init(character_name)
        if not self.file_data[character_name].config_weapon:
            self.file_data[character_name].config_weapon = {}
        data_ = self.file_data[character_name].config_weapon.get(config.parent, {})
        if value == "":
            if config.name in data_:
                del data_[config.name]
        else:
            if isinstance(config.default, bool):
                new_value = value == "true"
            else:
                value_class = type(config.default)
                new_value = value_class(value)
            data_[config.name] = new_value
        self.file_data[character_name].config_weapon[config.parent] = data_
        self.last_close(character_name)

    def get_weapon_config_enable(self, character_name: str, weapon_key: str) -> bool:
        if not self.file_data.get(character_name):
            return False
        if not self.file_data[character_name].config_weapon:
            return False
        return weapon_key in self.file_data[character_name].config_weapon

    def get_character_artifact_config_value(
        self, character_name: str, config_: WeaponConfig
    ) -> Any:
        if not self.file_data.get(character_name):
            return None
        if not self.file_data[character_name].artifact_config:
            return None
        data_ = self.file_data[character_name].artifact_config.get(config_.parent, None)
        if not data_:
            return None
        return data_.get(config_.name, None)

    def set_character_artifact_config_value(
        self, character_name: str, config: WeaponConfig, value: Any
    ):
        self.first_init(character_name)
        if not self.file_data[character_name].artifact_config:
            self.file_data[character_name].artifact_config = {}
        data_ = self.file_data[character_name].artifact_config.get(config.parent, {})
        if value == "":
            if config.name in data_:
                del data_[config.name]
        else:
            if isinstance(config.default, bool):
                new_value = value == "true"
            else:
                value_class = type(config.default)
                new_value = value_class(value)
            data_[config.name] = new_value
        self.file_data[character_name].artifact_config[config.parent] = data_
        self.last_close(character_name)

    def get_artifact_config_enable(
        self, character_name: str, artifact_key: str
    ) -> bool:
        if not self.file_data.get(character_name):
            return False
        if not self.file_data[character_name].artifact_config:
            return False
        return artifact_key in self.file_data[character_name].artifact_config


data = Data()
skill_data = SkillData(data.file_data)
