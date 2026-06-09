#pragma once

#include <gmock/gmock.h>
#include <windows.h>
#include <oaidl.h>

namespace rj2xcl {
namespace testing {

class MockTypeInfo : public ITypeInfo {
public:
    // IUnknown
    MOCK_METHOD(HRESULT, QueryInterface, (REFIID riid, void **ppvObject), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(ULONG, AddRef, (), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(ULONG, Release, (), (override, Calltype(STDMETHODCALLTYPE)));

    // ITypeInfo
    MOCK_METHOD(HRESULT, GetTypeAttr, (TYPEATTR **ppTypeAttr), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetTypeComp, (ITypeComp **ppTComp), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetFuncDesc, (UINT index, FUNCDESC **ppFuncDesc), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetVarDesc, (UINT index, VARDESC **ppVarDesc), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetNames, (MEMBERID memid, BSTR *rgBstrNames, UINT cMaxNames, UINT *pcNames), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetRefTypeOfImplType, (UINT index, HREFTYPE *pRefType), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetImplTypeFlags, (UINT index, INT *pImplTypeFlags), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetIDsOfNames, (LPOLESTR *rgszNames, UINT cNames, MEMBERID *pMemId), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, Invoke, (PVOID pvInstance, MEMBERID memid, WORD wFlags, DISPPARAMS *pDispParams, VARIANT *pVarResult, EXCEPINFO *pExcepInfo, UINT *puArgErr), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetDocumentation, (MEMBERID memid, BSTR *pBstrName, BSTR *pBstrDocString, DWORD *pdwHelpContext, BSTR *pBstrHelpFile), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetDllEntry, (MEMBERID memid, INVOKEKIND invKind, BSTR *pBstrDllName, BSTR *pBstrName, WORD *pwOrdinal), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetRefTypeInfo, (HREFTYPE hRefType, ITypeInfo **ppTInfo), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, AddressOfMember, (MEMBERID memid, INVOKEKIND invKind, PVOID *ppv), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, CreateInstance, (IUnknown *pUnkOuter, REFIID riid, PVOID *ppvObj), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetMops, (MEMBERID memid, BSTR *pBstrMops), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetContainingTypeLib, (ITypeLib **ppTLib, UINT *pIndex), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(void, ReleaseTypeAttr, (TYPEATTR *pTypeAttr), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(void, ReleaseFuncDesc, (FUNCDESC *pFuncDesc), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(void, ReleaseVarDesc, (VARDESC *pVarDesc), (override, Calltype(STDMETHODCALLTYPE)));
};

class MockDispatch : public IDispatch {
public:
    // IUnknown
    MOCK_METHOD(HRESULT, QueryInterface, (REFIID riid, void **ppvObject), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(ULONG, AddRef, (), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(ULONG, Release, (), (override, Calltype(STDMETHODCALLTYPE)));

    // IDispatch
    MOCK_METHOD(HRESULT, GetTypeInfoCount, (UINT *pctinfo), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetTypeInfo, (UINT iTInfo, LCID lcid, ITypeInfo **ppTInfo), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetIDsOfNames, (REFIID riid, LPOLESTR *rgszNames, UINT cNames, LCID lcid, DISPID *rgDispId), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, Invoke, (DISPID dispIdMember, REFIID riid, LCID lcid, WORD wFlags, DISPPARAMS *pDispParams, VARIANT *pVarResult, EXCEPINFO *pExcepInfo, UINT *puArgErr), (override, Calltype(STDMETHODCALLTYPE)));
};

class MockTypeLib : public ITypeLib {
public:
    // IUnknown
    MOCK_METHOD(HRESULT, QueryInterface, (REFIID riid, void **ppvObject), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(ULONG, AddRef, (), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(ULONG, Release, (), (override, Calltype(STDMETHODCALLTYPE)));

    // ITypeLib
    MOCK_METHOD(UINT, GetTypeInfoCount, (), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetTypeInfo, (UINT index, ITypeInfo **ppTInfo), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetTypeInfoType, (UINT index, TYPEKIND *pTKind), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetTypeInfoOfGuid, (REFGUID guid, ITypeInfo **ppTinfo), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetLibAttr, (TLIBATTR **ppTLibAttr), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetTypeComp, (ITypeComp **ppTComp), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, GetDocumentation, (INT index, BSTR *pBstrName, BSTR *pBstrDocString, DWORD *pdwHelpContext, BSTR *pBstrHelpFile), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, IsName, (LPOLESTR szNameBuf, ULONG lHashVal, BOOL *pfName), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(HRESULT, FindName, (LPOLESTR szNameBuf, ULONG lHashVal, ITypeInfo **ppTInfo, MEMBERID *rgMemId, USHORT *pcFound), (override, Calltype(STDMETHODCALLTYPE)));
    MOCK_METHOD(void, ReleaseTLibAttr, (TLIBATTR *pTLibAttr), (override, Calltype(STDMETHODCALLTYPE)));
};

}
}
