from restfulpy.orm.metadata import FieldInfo


def test_to_json_fieldinfo():
    age = FieldInfo(
        type_=(str, 400),
        pattern=('\\d+', 400),
        max_length=(2, 400),
        min_length=(1, 400),
        minimum=(1, 400),
        maximum=(99, 400),
        readonly=(True, 400),
        protected=(True, 400),
        not_none=(True, 400),
        required=(True, 400),
    )
    age_json_field_info = age.to_json()

    assert age_json_field_info['type'] == 'str'
    assert age_json_field_info['pattern'] == '\\d+'
    assert age_json_field_info['maxLength'] == 2
    assert age_json_field_info['minLength'] == 1
    assert age_json_field_info['minimum'] == 1
    assert age_json_field_info['maximum'] == 99
    assert age_json_field_info['readonly'] is True
    assert age_json_field_info['protected'] is True
    assert age_json_field_info['notNone'] is True
    assert age_json_field_info['required'] is True
