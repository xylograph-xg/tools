import AppKit
import ApplicationServices

struct Failure: Error { let code: String; let message: String }
func attr(_ e: AXUIElement, _ key: String) -> Any? { var v: CFTypeRef?; return AXUIElementCopyAttributeValue(e, key as CFString, &v) == .success ? v : nil }
func string(_ v: Any?) -> String { if let s = v as? String { return s }; if let n = v as? NSNumber { return n.stringValue }; return "" }
func children(_ e: AXUIElement) -> [AXUIElement] { attr(e, kAXChildrenAttribute) as? [AXUIElement] ?? [] }
func point(_ e: AXUIElement) -> CGPoint { guard let v = attr(e,kAXPositionAttribute), CFGetTypeID(v as CFTypeRef) == AXValueGetTypeID() else { return .zero }; var p = CGPoint.zero; AXValueGetValue(v as! AXValue,.cgPoint,&p); return p }
func size(_ e: AXUIElement) -> CGSize { guard let v = attr(e,kAXSizeAttribute), CFGetTypeID(v as CFTypeRef) == AXValueGetTypeID() else { return .zero }; var p = CGSize.zero; AXValueGetValue(v as! AXValue,.cgSize,&p); return p }
func windowNumber(_ w: AXUIElement, _ pid: pid_t) -> Int? {
    let p = point(w), s = size(w)
    let list = CGWindowListCopyWindowInfo([.optionAll,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] ?? []
    let candidates = list.filter { item in
        guard item[kCGWindowOwnerPID as String] as? Int == Int(pid), let b = item[kCGWindowBounds as String] as? NSDictionary,
              let r = CGRect(dictionaryRepresentation:b) else { return false }
        return abs(r.origin.x-p.x)<2 && abs(r.origin.y-p.y)<2 && abs(r.width-s.width)<2 && abs(r.height-s.height)<2
    }
    return candidates.count == 1 ? candidates[0][kCGWindowNumber as String] as? Int : nil
}
func menuMatches(_ e: AXUIElement, _ label: String, _ depth: Int = 0) -> [AXUIElement] {
    if depth>10 { return [] }; var out: [AXUIElement] = []
    if string(attr(e,kAXTitleAttribute)) == label { out.append(e) }
    for c in children(e) { out += menuMatches(c,label,depth+1) }; return out
}
var refs: [AXUIElement] = []; var nodes: [[String:Any]] = []; var exhausted = false
func walk(_ e: AXUIElement, _ parent: Int, _ depth: Int) {
    if refs.count >= 12000 || depth > 160 { exhausted = true; return }
    let i = refs.count; refs.append(e)
    var actions: CFArray?; AXUIElementCopyActionNames(e,&actions)
    let p = point(e), s = size(e)
    nodes.append(["id":i,"parent":parent,"role":string(attr(e,kAXRoleAttribute)),"title":string(attr(e,kAXTitleAttribute)),"description":string(attr(e,kAXDescriptionAttribute)),"value":string(attr(e,kAXValueAttribute)),"enabled":(attr(e,kAXEnabledAttribute) as? Bool) ?? true,"selected":(attr(e,kAXSelectedAttribute) as? Bool) ?? false,"x":Double(p.x),"y":Double(p.y),"width":Double(s.width),"height":Double(s.height),"actions":actions as? [String] ?? []])
    for c in children(e) { walk(c,i,depth+1) }
}
func matches(_ n: [String:Any], _ q: [String:Any]) -> Bool {
    for k in ["role","title","description","value"] { if let v = q[k] as? String, n[k] as? String != v { return false } }
    if let text = q["label"] as? String, !["title","description","value"].contains(where:{n[$0] as? String == text}) { return false }
    if (q["visible"] as? Bool) ?? true { if (n["width"] as? Double ?? 0) <= 1 || (n["height"] as? Double ?? 0) <= 1 { return false } }
    return true
}
func find(_ q: [String:Any]) throws -> Int {
    let found = nodes.indices.filter{matches(nodes[$0],q)}
    guard found.count == 1 else { throw Failure(code:"ambiguous_element",message:"Expected one matching element, found \(found.count)") }
    return found[0]
}
func postKey(_ code: CGKeyCode, _ flags: CGEventFlags = []) throws {
    guard let down = CGEvent(keyboardEventSource:nil,virtualKey:code,keyDown:true), let up = CGEvent(keyboardEventSource:nil,virtualKey:code,keyDown:false) else { throw Failure(code:"keyboard_failed",message:"Cannot create key events") }
    down.flags = flags; up.flags = []; down.post(tap:.cghidEventTap); usleep(20000); up.post(tap:.cghidEventTap); usleep(20000)
}
func output(_ value: [String:Any]) { let data = try! JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]); FileHandle.standardOutput.write(data); FileHandle.standardOutput.write(Data([10])) }
do {
    let data = FileHandle.standardInput.readDataToEndOfFile()
    let request = try JSONSerialization.jsonObject(with:data) as! [String:Any]
    let op = request["op"] as? String ?? "snapshot"
    guard AXIsProcessTrusted() else { throw Failure(code:"permission_required",message:"Accessibility permission is required for the launcher/host process") }
    let bundle = request["bundle_id"] as? String ?? "com.openai.codex"
    let apps = NSRunningApplication.runningApplications(withBundleIdentifier:bundle)
    guard apps.count == 1 else { throw Failure(code:"app_not_running",message:"Expected exactly one running app for \(bundle)") }
    let app = apps[0], root = AXUIElementCreateApplication(app.processIdentifier)
    AXUIElementSetMessagingTimeout(root,2)
    AXUIElementSetAttributeValue(root,"AXManualAccessibility" as CFString,kCFBooleanTrue)
    let windows = attr(root,kAXWindowsAttribute) as? [AXUIElement] ?? []
    if op == "windows" { output(["ok":true,"pid":Int(app.processIdentifier),"windows":windows.map{["id":Int(CFHash($0)),"cg_window_id":windowNumber($0,app.processIdentifier) as Any? ?? NSNull(),"title":string(attr($0,kAXTitleAttribute))]}]); exit(0) }
    if op == "new_window" {
        guard request["allow_foreground"] as? Bool == true else { throw Failure(code:"foreground_required",message:"Opening a window requires explicit foreground permission") }
        guard windows.count < (request["max_windows"] as? Int ?? 20) else { throw Failure(code:"window_limit",message:"Window limit reached; existing windows are protected") }
        guard let bar = attr(root,kAXMenuBarAttribute) else { throw Failure(code:"menu_unavailable",message:"No native menu bar") }
        let items = menuMatches(bar as! AXUIElement,"新建窗口")
        guard items.count == 1 else { throw Failure(code:"menu_unavailable",message:"New Window menu is not uniquely available") }
        guard AXUIElementPerformAction(items[0],kAXPressAction as CFString) == .success else { throw Failure(code:"new_window_failed",message:"Native New Window action failed") }
        output(["ok":true,"pid":Int(app.processIdentifier)]); exit(0)
    }
    let selected: AXUIElement
    if let wid = request["window_id"] as? Int {
        let match = windows.filter{Int(CFHash($0))==wid}
        guard match.count == 1 else { throw Failure(code:"window_changed",message:"Original window is not uniquely present") }; selected=match[0]
    } else {
        guard windows.count == 1 else { throw Failure(code:"ambiguous_window",message:"Supply window_id when multiple windows exist") }; selected=windows[0]
    }
    let wid=Int(CFHash(selected))
    guard windows.filter({Int(CFHash($0))==wid}).count == 1 else { throw Failure(code:"ambiguous_window",message:"Window identity collision; refusing ambiguous binding") }
    if let pid = request["expected_pid"] as? Int, pid != Int(app.processIdentifier) { throw Failure(code:"app_changed",message:"App process changed; original request requires manual reconciliation") }
    walk(selected,-1,0)
    guard !exhausted else { throw Failure(code:"tree_truncated",message:"Accessibility tree exceeded bounded traversal; refusing partial evidence") }
    if op == "snapshot" { output(["ok":true,"pid":Int(app.processIdentifier),"bundle_id":bundle,"window_count":windows.count,"window_id":wid,"nodes":nodes]); exit(0) }
    if op == "activate" {
        guard request["allow_foreground"] as? Bool == true else { throw Failure(code:"foreground_required",message:"Explicit foreground permission is required") }
        app.activate(options:[]); AXUIElementPerformAction(selected,kAXRaiseAction as CFString); usleep(250000)
        var focused: CFTypeRef?; AXUIElementCopyAttributeValue(root,kAXFocusedWindowAttribute as CFString,&focused)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == app.processIdentifier, let fw=focused,
              CFEqual(fw,selected) || refs.indices.contains(where:{nodes[$0]["role"] as? String == kAXSheetRole && CFEqual(fw,refs[$0])}) else { throw Failure(code:"focus_changed",message:"Original window/sheet did not become focused") }
        output(["ok":true,"pid":Int(app.processIdentifier),"window_id":wid]); exit(0)
    }
    guard request["allow_foreground"] as? Bool == true else { throw Failure(code:"foreground_required",message:"UI mutation requires explicit foreground permission") }
    let query = request["query"] as? [String:Any] ?? [:]
    let i = try find(query); let element = refs[i]
    guard nodes[i]["enabled"] as? Bool == true else { throw Failure(code:"element_disabled",message:"Target control is disabled") }
    if let exact = request["draft_equals"] as? String {
        let editor = try find(["role":kAXTextAreaRole,"label":"询问 ChatGPT"])
        guard [exact,exact+"\n"].contains(nodes[editor]["value"] as? String ?? "") else { throw Failure(code:"draft_changed",message:"Chat draft does not match the exact prepared request") }
    }
    if let expectedNames = request["attachment_names"] as? [String] {
        let editor = try find(["role":kAXTextAreaRole,"label":"询问 ChatGPT"])
        let composer = nodes[editor]["parent"] as? Int ?? -1
        guard composer >= 0 else { throw Failure(code:"attachment_structure",message:"Cannot bind attachment guards to composer") }
        var descendants: Set<Int> = [composer]
        for j in nodes.indices { if descendants.contains(nodes[j]["parent"] as? Int ?? -1) { descendants.insert(j) } }
        var names: [String] = []
        for j in descendants {
            let n = nodes[j], title = n["title"] as? String ?? "", desc = n["description"] as? String ?? "", value = n["value"] as? String ?? ""
            let label = title.isEmpty ? desc : title
            guard n["role"] as? String != "AXProgressIndicator", !label.contains("正在上传"), !label.contains("Uploading") else { throw Failure(code:"attachment_not_ready",message:"Attachment upload is still active; refusing send") }
            guard !["上传未成功","上传失败","Upload failed","已达上传上限"].contains(where:{(label+value).contains($0)}) else { throw Failure(code:"attachment_upload_failed",message:"Attachment failure/quota blocks send") }
            if n["role"] as? String == kAXButtonRole && label.hasPrefix("移除") {
                names.append(String(label.dropFirst(2)).trimmingCharacters(in:CharacterSet(charactersIn:" “”\"")))
            }
        }
        guard names.count == Set(names).count, names.sorted() == expectedNames.sorted() else { throw Failure(code:"attachment_mismatch",message:"Composer attachments changed before send") }
    }
    if let expected = request["expected_value"] as? String, nodes[i]["value"] as? String != expected { throw Failure(code:"element_changed",message:"Target value changed") }
    if op == "set_path" || op == "confirm_path" {
        guard request["allow_foreground"] as? Bool == true else { throw Failure(code:"foreground_required",message:"File selection requires foreground permission") }
        let parent = nodes[i]["parent"] as? Int ?? -1
        let grandparent = parent >= 0 ? nodes[parent]["parent"] as? Int ?? -1 : -1
        guard nodes[i]["role"] as? String == kAXTextFieldRole, parent >= 0, grandparent >= 0,
              nodes[parent]["role"] as? String == kAXSheetRole,
              nodes[grandparent]["role"] as? String == kAXSheetRole,
              nodes[grandparent]["description"] as? String == "打开" else { throw Failure(code:"file_panel_mismatch",message:"Path field does not belong to original Open sheet") }
        let path = request["path"] as? String ?? ""
        guard path.hasPrefix("/"), !path.contains("\n"), FileManager.default.fileExists(atPath:path) else { throw Failure(code:"invalid_file",message:"Expected existing absolute file path") }
        if op == "set_path" {
            guard AXUIElementSetAttributeValue(element,kAXValueAttribute as CFString,path as CFString) == .success,
                  string(attr(element,kAXValueAttribute)) == path else { throw Failure(code:"path_mismatch",message:"File path was not set exactly") }
        } else {
            guard string(attr(element,kAXValueAttribute)) == path else { throw Failure(code:"path_mismatch",message:"File path changed before confirmation") }
            guard AXUIElementPerformAction(element,"AXConfirm" as CFString) == .success else { throw Failure(code:"file_selection_failed",message:"Go To confirmation failed") }
        }
    } else if op == "click" {
        guard request["allow_foreground"] as? Bool == true else { throw Failure(code:"foreground_required",message:"Explicit pointer permission is required") }
        var focused: CFTypeRef?; AXUIElementCopyAttributeValue(root,kAXFocusedWindowAttribute as CFString,&focused)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == app.processIdentifier, let fw=focused, CFEqual(fw,selected) else { throw Failure(code:"focus_changed",message:"Exact target window must already be focused") }
        let p=point(element), s=size(element)
        guard s.width>1, s.height>1 else { throw Failure(code:"element_hidden",message:"Cannot click invisible control") }
        let location=CGPoint(x:p.x+s.width/2,y:p.y+s.height/2)
        guard let down=CGEvent(mouseEventSource:nil,mouseType:.leftMouseDown,mouseCursorPosition:location,mouseButton:.left),let up=CGEvent(mouseEventSource:nil,mouseType:.leftMouseUp,mouseCursorPosition:location,mouseButton:.left) else { throw Failure(code:"pointer_failed",message:"Cannot create pointer events") }
        down.post(tap:.cghidEventTap); usleep(30000); up.post(tap:.cghidEventTap)
    } else if op == "press" {
        let result = AXUIElementPerformAction(element,kAXPressAction as CFString)
        guard result == .success else { throw Failure(code:"press_failed",message:"AXPress returned \(result.rawValue)") }
    } else if op == "key" || op == "type" {
        guard request["allow_foreground"] as? Bool == true else { throw Failure(code:"foreground_required",message:"Explicit foreground permission is required") }
        app.activate(options:[]); AXUIElementPerformAction(selected,kAXRaiseAction as CFString); usleep(250000)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == app.processIdentifier else { throw Failure(code:"focus_changed",message:"Target app is not foreground") }
        let focused = AXUIElementSetAttributeValue(element,kAXFocusedAttribute as CFString,kCFBooleanTrue)
        guard op == "key" || focused == .success else { throw Failure(code:"focus_failed",message:"Cannot focus exact target editor") }
        var focusedWindow: CFTypeRef?
        AXUIElementCopyAttributeValue(root,kAXFocusedWindowAttribute as CFString,&focusedWindow)
        guard let fw=focusedWindow, CFEqual(fw,selected) || (op == "key" && refs.indices.contains(where: { nodes[$0]["role"] as? String == kAXSheetRole && CFEqual(fw,refs[$0]) })) else { throw Failure(code:"focus_changed",message:"Selected window did not become focused") }
        if op == "key" {
            var flags: CGEventFlags = []
            for modifier in request["modifiers"] as? [String] ?? [] {
                if modifier == "command" { flags.insert(.maskCommand) }
                else if modifier == "shift" { flags.insert(.maskShift) }
                else { throw Failure(code:"invalid_modifier",message:"Unsupported modifier") }
            }
            try postKey(CGKeyCode(request["keycode"] as? Int ?? 53),flags)
        }
        else {
            guard ["","询问 ChatGPT"].contains(string(attr(element,kAXValueAttribute)).trimmingCharacters(in:.whitespacesAndNewlines)) else { throw Failure(code:"draft_not_empty",message:"Existing draft is protected") }
            let text = request["text"] as? String ?? ""
            guard !text.isEmpty && text.utf16.count <= 32000 else { throw Failure(code:"invalid_prompt",message:"Prompt must contain 1..32000 UTF-16 units") }
            // Unicode events preserve whitespace and Chinese; no clipboard or IME keystroke translation.
            for ch in text {
                guard NSWorkspace.shared.frontmostApplication?.processIdentifier == app.processIdentifier else { throw Failure(code:"focus_changed",message:"Foreground app changed during typing; request was not sent") }
                var currentWindow: CFTypeRef?
                AXUIElementCopyAttributeValue(root,kAXFocusedWindowAttribute as CFString,&currentWindow)
                guard let cw=currentWindow, CFEqual(cw,selected) else { throw Failure(code:"focus_changed",message:"Window changed during typing; request was not sent") }
                let units = Array(String(ch).utf16)
                guard let down = CGEvent(keyboardEventSource:nil,virtualKey:0,keyDown:true), let up = CGEvent(keyboardEventSource:nil,virtualKey:0,keyDown:false) else { throw Failure(code:"keyboard_failed",message:"Cannot create Unicode event") }
                down.flags = []; up.flags = []
                units.withUnsafeBufferPointer { b in down.keyboardSetUnicodeString(stringLength:b.count,unicodeString:b.baseAddress); up.keyboardSetUnicodeString(stringLength:b.count,unicodeString:b.baseAddress) }
                down.post(tap:.cghidEventTap); usleep(6000); up.post(tap:.cghidEventTap); usleep(6000)
            }
        }
    } else { throw Failure(code:"invalid_operation",message:"Unsupported native operation") }
    output(["ok":true,"pid":Int(app.processIdentifier)])
} catch let e as Failure { output(["ok":false,"code":e.code,"message":e.message]); exit(2) }
catch { output(["ok":false,"code":"native_error","message":String(describing:error)]); exit(2) }
