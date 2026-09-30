/**
 * Copyright (c) 2026 RJ2XCL Project
 * 
 * This file is part of RJ2XCL.
 *
 * RJ2XCL is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RJ2XCL is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RJ2XCL.  If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#include "type_conversions.h"
#include "variable.pb.h"
#include <cstdint>

/**
 * @brief Maps and invokes COM automation objects for language service callbacks.
 *
 * Provides type library introspection, enum mapping, and dispatch invocation
 * for Excel COM objects accessed from R/Julia via the callback mechanism.
 */
class COMObjectMap {

public:

  /**
   * inner class representing a member function, including accessor
   * functions. get and set accessors are represented separately.
   */
  class MemberFunction
  {
  public:

    /**
     * this used to be a set of constants, in order to support then
     * by-reference method types PROPGETREF and PROPPUTREF. however we
     * never used those, they don't appear in the excel library. future
     * support could use a flag for reference semantics?
     */
    typedef enum {
      Undefined = 0,
      Method,
      PropertyGet,
      PropertyPut
    }
    CallType;

  public:
    /** type impacts call semantics */
    CallType call_type_;

    /** actual function name */
    std::string name_;

    /** arguments, as a list of names */
    std::vector< std::string > arguments_;

    /**
     * type info index for FUNCDESC (via GetFuncDesc). storing this means we don't
     * have to loop through the type lib.
     */
    uint32_t function_description_index_;

  public:
    MemberFunction() : call_type_(CallType::Undefined) {}

    /** copy ctor for containers */
    MemberFunction(const MemberFunction &rhs) {
      call_type_ = rhs.call_type_;
      name_ = rhs.name_;
      function_description_index_ = rhs.function_description_index_;
      for (auto arg : rhs.arguments_) arguments_.push_back(arg);
    }

  };

public:
  COMObjectMap() {} // : key_generator_(0xCa11) {}

protected:
  static std::string BSTRToString(CComBSTR &bstr) { return Convert::WideStringToUtf8(bstr.m_str, bstr.Length()); }

protected:
  typedef std::unordered_map < std::string, int > EnumValues;
  typedef std::unordered_map < std::string, EnumValues > Enums;

protected:
  std::unordered_map< std::basic_string<WCHAR>, std::vector< MemberFunction >> function_cache_;

protected:

  /**
  * because R only has 32-bit ints, it's a bit cumbersome to pass pointers around
  * as-is; also that seems like just generally a bad idea. we use a map instead.
  */
  // std::unordered_map<int32_t, ULONG_PTR> com_pointer_map_;

  /** base for map keys */
  // int32_t key_generator_;

public:

  /**
   * store pointer in map; add reference; return key
   */
   // int32_t MapCOMPointer(ULONG_PTR pointer);

   /**
    * return pointer for given key (lookup)
    */
    // ULONG_PTR UnmapCOMPointer(int32_t key);

    /**
     * remove pointer from map and call release().
     */
     // void RemoveCOMPointer(int32_t key);

  /**
   * @brief Releases a COM pointer and removes it from tracking.
   * @param pointer The COM pointer value to release.
   */
  void RemoveCOMPointer(ULONG_PTR pointer);

  /**
   * @brief Maps a COM enum into name-to-value pairs.
   * @param name Output: enum type name.
   * @param type_info COM type information for the enum.
   * @param type_attributes Type attributes describing the enum.
   * @return Map of enum member names to their integer values.
   */
  EnumValues MapEnum(std::string &name, CComPtr<ITypeInfo> type_info, TYPEATTR *type_attributes);

  /**
   * @brief Maps all enums accessible from a dispatch pointer.
   * @param dispatch_pointer COM dispatch pointer to introspect.
   * @param enums Output: map of enum names to their value maps.
   */
  void MapEnums(LPDISPATCH dispatch_pointer, Enums &enums);

  /**
   * @brief Maps a COM interface's member functions.
   * @param name Output: interface name.
   * @param members Output: vector of member function descriptors.
   * @param typeinfo COM type information for the interface.
   * @param type_attributes Type attributes describing the interface.
   */
  void MapInterface(std::string &name, std::vector< MemberFunction > &members, CComPtr<ITypeInfo> typeinfo, TYPEATTR *type_attributes);

  /**
   * @brief Maps a COM object's members, optionally filtering by name.
   * @param dispatch_pointer COM dispatch pointer to introspect.
   * @param member_list Output: vector of member function descriptors.
   * @param match_name Optional name filter (empty = map all).
   */
  void MapObject(IDispatch *dispatch_pointer, std::vector< MemberFunction > &member_list, CComBSTR &match_name);

  /**
   * @brief Retrieves the CoClass type info for a dispatch pointer.
   * @param coclass_ref Output: pointer to the CoClass ITypeInfo.
   * @param dispatch_pointer COM dispatch pointer.
   * @return true if CoClass was found.
   */
  bool GetCoClassForDispatch(ITypeInfo **coclass_ref, IDispatch *dispatch_pointer);

  /**
   * @brief Gets the default interface name for a dispatch pointer.
   * @param name Output: interface name.
   * @param dispatch_pointer COM dispatch pointer.
   * @return true if interface name was resolved.
   */
  bool GetObjectInterface(CComBSTR &name, IDispatch *dispatch_pointer);

public:

  /**
   * @brief Wraps a dispatch pointer in a Protobuf response for return to language.
   * @param response Output Protobuf response to populate.
   * @param dispatch_pointer COM dispatch pointer to wrap.
   */
  void DispatchResponse(RJ2XCLBuffers::CallResponse &response, const LPDISPATCH dispatch_pointer);

  /**
   * @brief Serializes a COM object's interface into a Protobuf Variable.
   * @param variable Output Protobuf Variable to populate.
   * @param dispatch_pointer COM dispatch pointer to introspect.
   * @param enums If true, includes enum definitions (can be very large).
   */
  void DispatchToVariable(RJ2XCLBuffers::Variable *variable, LPDISPATCH dispatch_pointer, bool enums = false);

  /**
   * @brief Invokes a COM property put (set) accessor.
   * @param callback The composite function call describing the property and value.
   * @param response Output Protobuf response.
   */
  void InvokeCOMPropertyPut(const RJ2XCLBuffers::CompositeFunctionCall &callback, RJ2XCLBuffers::CallResponse &response);

  /**
   * @brief Invokes a COM function or property get accessor.
   * @param callback The composite function call describing the method and arguments.
   * @param response Output Protobuf response.
   */
  void InvokeCOMFunction(const RJ2XCLBuffers::CompositeFunctionCall &callback, RJ2XCLBuffers::CallResponse &response);

};

