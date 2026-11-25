"""Pure helpers for building breeder family trees."""

from collections import defaultdict
from datetime import date

MAX_DEPTH = 6


def _sort_key(cat):
    return (getattr(cat, "birth_date", None) or date.max, cat.pk)


def _reference(cat):
    if cat is None:
        return None
    return {
        "id": cat.pk,
        "name": cat.name,
        "sex": cat.sex,
        "breed": cat.breed.name,
        "photo_url": cat.photo_url,
        "status": cat.status,
        "birth_date": getattr(cat, "birth_date", None),
    }


def _node(cat, mother, father):
    node = _reference(cat)
    node["mother"] = _reference(mother)
    node["father"] = _reference(father)
    node["children"] = []
    return node


def build_family_tree(cats, max_depth=MAX_DEPTH):
    """
    Group cats into families and build one nested tree per family.

    The mother is the main branch; a father from the same family is kept
    as a reference on the child, so a cat is never duplicated in the tree.
    """
    cats = list(cats)
    by_id = {cat.pk: cat for cat in cats}
    if not by_id:
        return []

    ids = {}
    parents = {}
    children = defaultdict(list)

    def find(pk):
        while ids[pk] != pk:
            ids[pk] = ids[ids[pk]]
            pk = ids[pk]
        return pk

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            ids[rb] = ra

    for cat in cats:
        ids[cat.pk] = cat.pk

    for cat in cats:
        mother = by_id.get(getattr(cat, "mother_id", None))
        father = by_id.get(getattr(cat, "father_id", None))
        parents[cat.pk] = (mother, father)
        for parent in (mother, father):
            if parent is not None:
                union(cat.pk, parent.pk)
        primary = mother or father
        if primary is not None:
            children[primary.pk].append(cat)

    components = defaultdict(list)
    for pk, cat in by_id.items():
        components[find(pk)].append(cat)

    def node(cat, depth, visited):
        result = _node(cat, *parents[cat.pk])
        if depth < max_depth:
            for child in sorted(children.get(cat.pk, []), key=_sort_key):
                if child.pk in visited:
                    continue
                visited.add(child.pk)
                result["children"].append(node(child, depth + 1, visited))
        return result

    def depth_of(result):
        if not result["children"]:
            return 1
        return 1 + max(depth_of(child) for child in result["children"])

    families = []
    for members in components.values():
        members = sorted(members, key=_sort_key)
        member_ids = {cat.pk for cat in members}
        roots = [
            cat for cat in members
            if getattr(cat, "mother_id", None) not in member_ids
            and getattr(cat, "father_id", None) not in member_ids
        ]
        if not roots:
            roots = [members[0]]
        roots = sorted(roots, key=_sort_key)
        primary = next((cat for cat in roots if cat.sex == "female"), roots[0])

        visited = {primary.pk}
        tree = node(primary, 1, visited)
        families.append({
            "id": min(cat.pk for cat in roots),
            "roots": [_reference(cat) for cat in roots],
            "tree": tree,
            "cats_count": len(members),
            "generations": depth_of(tree),
        })

    return sorted(families, key=lambda family: family["id"])
