#!/usr/bin/python
#
# Copyright 2020 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# gen_restricted_traces.py:
#   Generates integration code for the restricted trace tests.

import fnmatch
import json
import os
import sys

gni_template = """# GENERATED FILE - DO NOT EDIT.
# Generated by {script_name} using data from {data_source_name}
#
# Copyright 2020 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# A list of all restricted trace tests, paired with their context.
# Can be consumed by tests/BUILD.gn.

angle_restricted_traces = [
{test_list}
]
"""

header_template = """// GENERATED FILE - DO NOT EDIT.
// Generated by {script_name} using data from {data_source_name}
//
// Copyright 2020 The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// {filename}: Types and enumerations for trace tests.

#ifndef ANGLE_RESTRICTED_TRACES_H_
#define ANGLE_RESTRICTED_TRACES_H_

#include <cstdint>
#include <vector>
#include <KHR/khrplatform.h>

// See util/util_export.h for details on import/export labels.
#if !defined(ANGLE_TRACE_EXPORT)
#    if defined(_WIN32)
#        if defined(ANGLE_TRACE_IMPLEMENTATION)
#            define ANGLE_TRACE_EXPORT __declspec(dllexport)
#        else
#            define ANGLE_TRACE_EXPORT __declspec(dllimport)
#        endif
#    elif defined(__GNUC__)
#        define ANGLE_TRACE_EXPORT __attribute__((visibility("default")))
#    else
#        define ANGLE_TRACE_EXPORT
#    endif
#endif  // !defined(ANGLE_TRACE_EXPORT)

namespace trace_angle
{{
using GenericProc = void (*)();
using LoadProc    = GenericProc(KHRONOS_APIENTRY *)(const char *);
ANGLE_TRACE_EXPORT void LoadGLES(LoadProc loadProc);
}}  // namespace trace_angle

namespace angle
{{
enum class RestrictedTraceID
{{
{trace_ids}, InvalidEnum, EnumCount = InvalidEnum
}};

using ReplayFunc = void (*)(uint32_t);
using ResetFunc = void (*)();
using SetupFunc = void (*)();
using DecompressFunc = uint8_t *(*)(const std::vector<uint8_t> &);
using SetBinaryDataDirFunc = void (*)(const char *);

static constexpr size_t kTraceInfoMaxNameLen = 32;

struct TraceInfo
{{
    uint32_t startFrame;
    uint32_t endFrame;
    uint32_t drawSurfaceWidth;
    uint32_t drawSurfaceHeight;
    char name[kTraceInfoMaxNameLen];
}};

using DecompressCallback = uint8_t *(*)(const std::vector<uint8_t> &);

ANGLE_TRACE_EXPORT const TraceInfo &GetTraceInfo(RestrictedTraceID traceID);
ANGLE_TRACE_EXPORT void ReplayFrame(RestrictedTraceID traceID, uint32_t frameIndex);
ANGLE_TRACE_EXPORT void ResetReplay(RestrictedTraceID traceID);
ANGLE_TRACE_EXPORT void SetupReplay(RestrictedTraceID traceID);
ANGLE_TRACE_EXPORT void SetBinaryDataDir(RestrictedTraceID traceID, const char *dataDir);
ANGLE_TRACE_EXPORT void SetBinaryDataDecompressCallback(RestrictedTraceID traceID, DecompressCallback callback);
}}  // namespace angle

#endif  // ANGLE_RESTRICTED_TRACES_H_
"""

source_template = """// GENERATED FILE - DO NOT EDIT.
// Generated by {script_name} using data from {data_source_name}
//
// Copyright 2020 The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// {filename}: Types and enumerations for trace tests.

#include "{filename}.h"

#include "common/PackedEnums.h"

{trace_includes}

namespace angle
{{
namespace
{{
constexpr angle::PackedEnumMap<RestrictedTraceID, TraceInfo> kTraceInfos = {{
{trace_infos}
}};
}}

const TraceInfo &GetTraceInfo(RestrictedTraceID traceID)
{{
    return kTraceInfos[traceID];
}}

void ReplayFrame(RestrictedTraceID traceID, uint32_t frameIndex)
{{
    switch (traceID)
    {{
{replay_func_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

void ResetReplay(RestrictedTraceID traceID)
{{
    switch (traceID)
    {{
{reset_func_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

void SetupReplay(RestrictedTraceID traceID)
{{
    switch (traceID)
    {{
{setup_func_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

void SetBinaryDataDir(RestrictedTraceID traceID, const char *dataDir)
{{
    switch (traceID)
    {{
{set_binary_data_dir_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

void SetBinaryDataDecompressCallback(RestrictedTraceID traceID, DecompressCallback callback)
{{
    switch (traceID)
    {{
{decompress_callback_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}
}}  // namespace angle
"""


def reject_duplicate_keys(pairs):
    found_keys = {}
    for key, value in pairs:
        if key in found_keys:
            raise ValueError("duplicate key: %r" % (key,))
        else:
            found_keys[key] = value
    return found_keys


def gen_gni(traces, gni_file, format_args):
    format_args["test_list"] = ",\n".join(
        ['"%s %s"' % (trace, get_context(trace)) for trace in traces])
    gni_data = gni_template.format(**format_args)
    with open(gni_file, "w") as out_file:
        out_file.write(gni_data)
    return True


def get_trace_info(trace):
    info = [
        "%s::kReplayFrameStart", "%s::kReplayFrameEnd", "%s::kReplayDrawSurfaceWidth",
        "%s::kReplayDrawSurfaceHeight", "\"%s\""
    ]
    return ", ".join([element % trace for element in info])


def get_context(trace):
    "Returns the context number used by trace header file"
    for file in os.listdir(trace):
        # Load up the only header present for each trace
        if fnmatch.fnmatch(file, '*.h'):
            # Strip the extension to isolate the context
            context = file[len(file) - 3]
            assert context.isdigit() == True, "Failed to find trace context number"
            assert file[len(file) - 4].isdigit() == False, "Context number is higher than 9"
            return context


def get_cases(traces, function, args):
    funcs = [
        "case RestrictedTraceID::%s: %s::%s(%s); break;" % (trace, trace, function, args)
        for trace in traces
    ]
    return "\n".join(funcs)


def get_header_name(trace):
    return "%s/%s_capture_context%s.h" % (trace, trace, get_context(trace))


def get_source_name(trace):
    return "%s/%s_capture_context%s.cpp" % (trace, trace, get_context(trace))


def get_sha1_name(trace):
    return "%s.tar.gz.sha1" % trace


def get_cases_with_context(traces, function_start, function_end, args):
    funcs = [
        "case RestrictedTraceID::%s: %s::%s%s%s(%s); break;" %
        (trace, trace, function_start, get_context(trace), function_end, args) for trace in traces
    ]
    return "\n".join(funcs)


def gen_header(header_file, format_args):
    header_data = header_template.format(**format_args)
    with open(header_file, "w") as out_file:
        out_file.write(header_data)
    return True


def gen_source(source_file, format_args):
    source_data = source_template.format(**format_args)
    with open(source_file, "w") as out_file:
        out_file.write(source_data)
    return True


def gen_git_ignore(traces):
    ignores = ['%s/' % trace for trace in traces] + ['%s.tar.gz' % trace for trace in traces]
    with open('.gitignore', 'w') as out_file:
        out_file.write('\n'.join(sorted(ignores)))
    return True


def read_json(json_file):
    with open(json_file) as map_file:
        return json.loads(map_file.read(), object_pairs_hook=reject_duplicate_keys)


def main():
    json_file = 'restricted_traces.json'
    gni_file = 'restricted_traces_autogen.gni'
    header_file = 'restricted_traces_autogen.h'
    source_file = 'restricted_traces_autogen.cpp'

    json_data = read_json(json_file)
    if 'traces' not in json_data:
        print('Trace data missing traces key.')
        return 1
    traces = json_data['traces']

    # auto_script parameters.
    if len(sys.argv) > 1:
        inputs = [json_file] + [get_sha1_name(trace) for trace in traces]
        outputs = [gni_file, header_file, source_file, '.gitignore']

        if sys.argv[1] == 'inputs':
            print(','.join(inputs))
        elif sys.argv[1] == 'outputs':
            print(','.join(outputs))
        else:
            print('Invalid script parameters.')
            return 1
        return 0

    format_args = {
        "script_name": __file__,
        "data_source_name": json_file,
    }

    if not gen_gni(traces, gni_file, format_args):
        print('.gni file generation failed.')
        return 1

    includes = ["#include \"%s\"" % get_header_name(trace) for trace in traces]
    trace_infos = [
        "{RestrictedTraceID::%s, {%s}}" % (trace, get_trace_info(trace)) for trace in traces
    ]

    format_args["filename"] = "restricted_traces_autogen"
    format_args["trace_ids"] = ",\n".join(traces)
    format_args["trace_includes"] = "\n".join(includes)
    format_args["trace_infos"] = ",\n".join(trace_infos)
    format_args["replay_func_cases"] = get_cases_with_context(traces, "ReplayContext", "Frame",
                                                              "frameIndex")
    format_args["reset_func_cases"] = get_cases_with_context(traces, "ResetContext", "Replay", "")
    format_args["setup_func_cases"] = get_cases_with_context(traces, "SetupContext", "Replay", "")
    format_args["set_binary_data_dir_cases"] = get_cases(traces, "SetBinaryDataDir", "dataDir")
    format_args["decompress_callback_cases"] = get_cases(traces, "SetBinaryDataDecompressCallback",
                                                         "callback")
    if not gen_header(header_file, format_args):
        print('.h file generation failed.')
        return 1

    if not gen_source(source_file, format_args):
        print('.cpp file generation failed.')
        return 1

    if not gen_git_ignore(traces):
        print('.gitignore file generation failed')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
