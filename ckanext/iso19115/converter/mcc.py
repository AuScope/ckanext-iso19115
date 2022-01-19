from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .. import types


@dataclass
class MD_Identifier:
    code: str
    authority: Optional[types.cit.CI_Citation] = None
    codeSpace: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None

@dataclass
class MD_BrowseGraphic:
    fileName: str
    fileDescription: Optional[str] = None
    fileType: Optional[str] = None
    imageConstraints: list[types.mco.MD_Constraints] = field(default_factory=list)
    linkage: list[types.cit.CI_OnlineResource] = field(default_factory=list)


@dataclass
class MD_Scope:
    level: str # codelist("MD_ScopeCode")
    # extent: list[types.gex.EX_Extent] = field(default_factory=list)
    levelDescription: list[MD_ScopeDescription] = field(default_factory=list)


@dataclass
class MD_ScopeDescription:
    attributes: str
    features: str
    featureInstances: str
    attributeInstances: str
    dataset: str
    other: str
